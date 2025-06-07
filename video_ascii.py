import os
import imageio
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from tqdm import tqdm
import gc
import numpy as np
import warnings

# Suppress specific runtime warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

ASCII_CHARS = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
BLOCK_CHARS = [' ', '░', '▒', '▓', '█']

def pixel_to_ascii_gray(gray, style="grayscale"):
    """Convert pixel value to ASCII character with bounds checking"""
    chars = BLOCK_CHARS if style == "blocks" else ASCII_CHARS
    gray = max(0, min(255, gray))  # Ensure gray is within 0-255 range
    index = gray * (len(chars) - 1) // 255
    index = max(0, min(len(chars) - 1, index))  # Ensure index is valid
    return chars[index]

def get_char_size(font):
    bbox = font.getbbox("A")
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def frame_to_ascii_image(frame, style="colored", font=None):
    if font is None:
        font = ImageFont.load_default()
    
    image = Image.fromarray(frame).convert("RGB")
    width, height = image.size
    char_w, char_h = get_char_size(font)

    # Convert to numpy array for faster processing
    pixels = np.array(image)
    
    # Create output image
    out_image = Image.new("RGB", (width * char_w, height * char_h), "black")
    draw = ImageDraw.Draw(out_image)

    if style == "colored":
        # Vectorized calculations for colored style
        gray_values = np.sum(pixels, axis=2) // 3  # Integer division for grayscale
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[y, x]
                gray = gray_values[y, x]
                ch = pixel_to_ascii_gray(gray, style)
                draw.text((x * char_w, y * char_h), ch, fill=(int(r), int(g), int(b)))
    else:
        # Process grayscale styles
        if style == "grayscale":
            gray_pixels = np.mean(pixels, axis=2).astype(np.uint8)
        elif style == "inverted":
            gray_pixels = 255 - np.mean(pixels, axis=2).astype(np.uint8)
        elif style == "blocks":
            gray_pixels = np.mean(pixels, axis=2).astype(np.uint8)
        
        for y in range(height):
            for x in range(width):
                gray = gray_pixels[y, x]
                ch = pixel_to_ascii_gray(gray, style)
                draw.text((x * char_w, y * char_h), ch, fill=(255, 255, 255))

    return out_image

def convert_video_to_ascii(input_video, output_video, style="colored", fps=15, max_frames=None):
    temp_files = []
    try:
        reader = imageio.get_reader(input_video, "ffmpeg")
        font = ImageFont.load_default()
        
        # Get video metadata
        meta = reader.get_meta_data()
        orig_w, orig_h = meta['size']
        char_w, char_h = get_char_size(font)
        
        # Calculate total frames safely
        try:
            total_frames = reader.count_frames()
        except:
            # If count_frames isn't available, estimate from duration
            total_frames = int(meta['duration'] * fps)
        
        if max_frames and max_frames < total_frames:
            total_frames = max_frames

        print(f"🎞️ Converting {total_frames} frames to ASCII...")

        # Process in chunks to avoid memory issues
        chunk_size = min(30, total_frames)
        frame_count = 0
        chunk_index = 0
        
        with tqdm(total=total_frames) as pbar:
            while frame_count < total_frames:
                current_chunk = []
                processed_in_chunk = 0
                
                for _ in range(chunk_size):
                    if frame_count >= total_frames:
                        break
                    
                    try:
                        frame = reader.get_next_data()
                        img = frame_to_ascii_image(frame, style=style, font=font)
                        current_chunk.append(np.array(img))
                        frame_count += 1
                        processed_in_chunk += 1
                        pbar.update(1)
                    except StopIteration:
                        break
                
                if current_chunk:
                    temp_file = f"temp_chunk_{chunk_index}.mp4"
                    with imageio.get_writer(temp_file, fps=fps, codec='libx264') as writer:
                        for img in current_chunk:
                            writer.append_data(img)
                    temp_files.append(temp_file)
                    chunk_index += 1
                    gc.collect()

        # Combine all chunks
        if temp_files:
            print("🔗 Combining temporary files...")
            with imageio.get_writer(output_video, fps=fps, codec='libx264') as writer:
                for temp_file in temp_files:
                    with imageio.get_reader(temp_file) as chunk_reader:
                        for frame in chunk_reader:
                            writer.append_data(frame)
                    os.remove(temp_file)

        print(f"✅ Saved ASCII video to: {output_video}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Cleanup any remaining temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Path to input video")
    parser.add_argument("--style", default="colored", choices=["colored", "grayscale", "inverted", "blocks"])
    parser.add_argument("--fps", type=int, default=15, help="Output frames per second")
    parser.add_argument("--max_frames", type=int, help="Limit number of frames to process")
    parser.add_argument("--output", help="Output video name (default auto)")
    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.video))[0]
    output = args.output or f"{base_name}-{args.style}-ascii.mp4"
    
    convert_video_to_ascii(
        args.video, 
        output, 
        style=args.style, 
        fps=args.fps, 
        max_frames=args.max_frames
    )
