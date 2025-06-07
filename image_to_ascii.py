
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import os

ASCII_CHARS = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
BLOCK_CHARS = [' ', '░', '▒', '▓', '█']

def pixel_to_ascii_gray(gray, style="grayscale"):
    if style == "blocks":
        chars = BLOCK_CHARS
    else:
        chars = ASCII_CHARS
    idx = gray * (len(chars) - 1) // 255
    return chars[idx]

def get_char_size(font):
    bbox = font.getbbox("A")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

def image_to_ascii_image(image_path, output_path, style="colored"):
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    # Nâng sáng cho ảnh màu để tránh tối quá khi dùng style colored
    if style == "colored":
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.3)

    font = ImageFont.load_default()
    char_width, char_height = get_char_size(font)

    out_image = Image.new("RGB", (char_width * width, char_height * height), color="black")
    draw = ImageDraw.Draw(out_image)

    pixels = list(image.getdata())

    # Nếu style là grayscale hoặc inverted hoặc blocks thì chuyển pixel sang grayscale trước
    if style == "grayscale":
        gray_pixels = [int(sum(px) / 3) for px in pixels]
    elif style == "inverted":
        gray_pixels = [255 - int(sum(px) / 3) for px in pixels]
    elif style == "blocks":
        gray_pixels = [int(sum(px) / 3) for px in pixels]
    else:  # colored
        gray_pixels = None

    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if style == "colored":
                r, g, b = pixels[idx]
                gray = int((r + g + b) / 3)
                char = pixel_to_ascii_gray(gray, style)
                draw.text((x * char_width, y * char_height), char, fill=(r, g, b))
            else:
                gray = gray_pixels[idx]
                char = pixel_to_ascii_gray(gray, style)
                draw.text((x * char_width, y * char_height), char, fill=(255, 255, 255))

    out_image.save(output_path)
    print(f"✅ Saved ASCII art image with style '{style}' to {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert image to ASCII art image with styles")
    parser.add_argument("input_image", help="Path to input image")
    parser.add_argument("--style", default="colored", choices=["colored", "grayscale", "inverted", "blocks"],
                        help="ASCII art style")
    parser.add_argument("--output", help="Path to output image (PNG)")
    args = parser.parse_args()

    out_path = args.output
    if not out_path:
        base, ext = os.path.splitext(os.path.basename(args.input_image))
        out_path = f"{base}-{args.style}-ascii.png"

    image_to_ascii_image(args.input_image, out_path, style=args.style)
