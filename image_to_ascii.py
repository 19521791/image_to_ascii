from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import os
import math

BLOCK_CHARS = [' ', '▁','▂','▃','▄','▅','▆','▇','█']
ASCII_CHARS = [' ', '·', ':', ';', '=', '+', '*', '#', '%', '@']
SKETCH_CHARS = [' ', '¸', '·', '˙', '˚', '¨', '´', '˜', 'ˆ', '˝']
VINTAGE_CHARS = [' ', '░', '▒', '▓', '█']
NEON_CHARS = [' ', '⡀', '⡄', '⡆', '⡇', '⣇', '⣧', '⣷', '⣿']
PIXEL_CHARS = [' ', '▘','▝','▀','▖','▌','▞','▛','▗','▚','▐','▜','▄','▙','▟','█']

STYLES = {
    'colored': {
        'chars': BLOCK_CHARS,
        'color': True,
        'bg': 'black',
        'preprocess': lambda img: ImageEnhance.Brightness(
            img.point(lambda x: int(x*1.8) if x < 85 else x)
        ).enhance(1.1)
    },
    
    'grayscale': {
        'chars': ASCII_CHARS,
        'color': False,
        'bg': 'black',
        'preprocess': lambda img: img.convert('L').point(
            lambda x: int(math.pow(x/255, 0.7)*255)
        )
    },
    
    'inverted': {
        'chars': ASCII_CHARS,
        'color': False,
        'bg': 'white',
        'preprocess': lambda img: ImageOps.invert(
            img.convert('L').point(lambda x: int(math.pow(x/255, 0.6)*255))
        ).convert('RGB')
    },
    
    'vintage': {
        'chars': VINTAGE_CHARS,
        'color': True,
        'preprocess': lambda img: ImageEnhance.Color(
            img.point(lambda x: int(x*1.6) if x < 64 else x)
        ).enhance(0.7)
    },
    
    'neon': {
        'chars': NEON_CHARS,
        'color': True,
        'preprocess': lambda img: ImageEnhance.Contrast(
            img.point(lambda x: 0 if x < 16 else x)
        ).enhance(1.8)
    },
    
    'comic': {
        'chars': [' ', '.', ':', '*', '+', '=', '≡', '▓', '█'],
        'color': True,
        'preprocess': lambda img: ImageEnhance.Contrast(
            img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            .point(lambda x: int(x*1.4) if x < 96 else x)
        ).enhance(2.0)
    },
    
    'handdrawn': {
        'chars': [' ', '·', ':', '-', '=', '+', '*', '#', '@'],
        'color': False,
        'preprocess': lambda img: img.convert('L')
                                 .filter(ImageFilter.FIND_EDGES)
                                 .point(lambda x: 255 if x > 30 else 0)
                                 .filter(ImageFilter.SMOOTH)
                                 .convert('RGB')
    },
    
    'cyberpunk': {
        'chars': [' ', '·', ':', '-', '=', '*', '+', '✦', '✶', '█'],
        'color': True,
        'bg': 'black',
        'preprocess': lambda img: ImageEnhance.Color(
            ImageEnhance.Contrast(
                img.point(lambda x: int(x*1.5) if x < 85 else x)
            ).enhance(1.8)
        ).enhance(1.8)
    },
    
    'pixelgame': {
        'chars': PIXEL_CHARS,
        'color': True,
        'bg': 'black',
        'preprocess': lambda img: img.resize(
            (img.width//5, img.height//5), Image.NEAREST
        ).resize(
            (img.width, img.height), Image.NEAREST
        ).point(lambda x: int(x*1.3) if x < 128 else x)
    }
}

def gamma_correction(luminance, gamma=0.6):
    return int(math.pow(luminance/255, gamma) * 255)

def get_block_char(luminance, chars):
    adjusted = gamma_correction(luminance)
    idx = min(len(chars)-1, max(0, adjusted * (len(chars)-1) // 255))
    return chars[idx]

def adjust_channel(c):
    return min(255, int(c * 1.2)) if c < 128 else c

def image_to_ascii(image_path, output_path, style='colored', block_size=3):
    if style not in STYLES:
        raise ValueError(f"Style không hợp lệ. Chọn: {', '.join(STYLES.keys())}")
    
    style_config = STYLES[style]
    img = Image.open(image_path).convert("RGB")  
    
    
    if 'preprocess' in style_config:
        img = style_config['preprocess'](img)
    
    
    if style_config['color']:
        img = img.convert("RGB")
    else:
        img = img.convert("L")
    
    width, height = img.size
    new_width = width // block_size
    new_height = height // block_size

    
    try:
        font = ImageFont.truetype("Courier.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    char_width, char_height = get_char_size(font)
    out_img = Image.new("RGB", 
                       (char_width * new_width, char_height * new_height), 
                       color=style_config.get('bg', 'black'))
    draw = ImageDraw.Draw(out_img)
    
    pixels = list(img.getdata())
    
    for y in range(new_height):
        for x in range(new_width):
            
            block_pixels = []
            for dy in range(block_size):
                for dx in range(block_size):
                    px = x * block_size + dx
                    py = y * block_size + dy
                    if px < width and py < height:
                        block_pixels.append(pixels[py * width + px])
            
            if not block_pixels:
                continue
                
            if style_config['color']:
                
                avg_r = sum(p[0] for p in block_pixels) // len(block_pixels)
                avg_g = sum(p[1] for p in block_pixels) // len(block_pixels)
                avg_b = sum(p[2] for p in block_pixels) // len(block_pixels)

                avg_r = adjust_channel(avg_r)
                avg_g = adjust_channel(avg_g)
                avg_b = adjust_channel(avg_b)
                
                luminance = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b
                color = (avg_r, avg_g, avg_b)
            else:
                
                luminance = sum(block_pixels) // len(block_pixels)
                color = (0, 0, 0) if style_config.get('bg', 'black') == 'white' else (255, 255, 255)
            
            char = get_block_char(luminance, style_config['chars'])
            
            draw.text((x * char_width, y * char_height), char, fill=color)
    
    out_img.save(output_path, quality=95)
    print(f"✅ Đã tạo ASCII art: {style} (block: {block_size})")

def get_char_size(font):
    bbox = font.getbbox("█")
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tạo ASCII Art từ ảnh")
    parser.add_argument("input_image", help="Đường dẫn ảnh đầu vào")
    parser.add_argument("--style", default="colored", choices=STYLES.keys(),
                      help=f"Kiểu ASCII: {', '.join(STYLES.keys())}")
    parser.add_argument("--block", type=int, default=3,
                      help="Kích thước block (1-6)")
    parser.add_argument("--output", help="Đường dẫn đầu ra (phải có phần mở rộng .png)")
    
    args = parser.parse_args()

    if args.output and os.path.isdir(args.output):
        base_name = os.path.splitext(os.path.basename(args.input_image))[0]
        out_path = os.path.join(args.output, f"{base_name}-{args.style}.png")
    elif args.output:
        out_path = args.output
    else:
        out_path = f"{os.path.splitext(args.input_image)[0]}-{args.style}.png"
    
    if not out_path.lower().endswith('.png'):
        out_path += '.png'
    
    image_to_ascii(args.input_image, out_path, args.style, args.block)
