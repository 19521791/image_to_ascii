
from PIL import Image, ImageOps, ImageEnhance
import cv2
import os
import imgkit
import shutil
import sys

def video_to_images(path):
    os.mkdir('Images')
    video = cv2.VideoCapture(path)
    fps = video.get(cv2.CAP_PROP_FPS)
    success, image = video.read()
    counter = 1
    while success:
        cv2.imwrite("Images/Image{0}.jpg".format(str(counter)), image)
        success, image = video.read()
        counter += 1
    return fps, (counter - 1)

def get_image(image_path):
    initial_image = Image.open(image_path)
    width, height = initial_image.size
    initial_image = initial_image.resize((round(width * 1.05), height))
    return initial_image

def pixelate_image(image, final_width=200):
    width, height = image.size
    final_height = int((height * final_width) / width)
    image = image.resize((final_width, final_height))
    return image

def grayscale_image(image):
    image_bw = ImageOps.grayscale(image)
    return image_bw

def ascii_conversion(bw_image, ascii_string=[" ", ".", ":", "-", "=", "+", "*", "#", "%", "@", "&"]):
    pixels = bw_image.getdata()
    ascii_image_list = []
    for pixel in pixels:
        ascii_converted = int((pixel * len(ascii_string)) / 256)
        ascii_image_list.append(ascii_string[ascii_converted])
    return ascii_image_list

def get_color(image):
    pixels = image.getdata()
    return pixels

def print_ascii(ascii_list, image, color, image_pos):
    os.makedirs('HtmlImages', exist_ok=True)
    file = open('HtmlImages/Html{0}.html'.format(str(image_pos)), "w")
    file.write("""
     <!DOCTYPE html>
     <html>
        <body style='background-color:black'>
        <pre style='display: inline-block; border-width: 4px 6px; border-color: black; border-style: solid; background-color:black; font-size: 32px ;font-face: Montserrat;font-weight: bold;line-height:60%'>""")

    width, height = image.size
    counter = 0
    for j in ascii_list:
        color_hex = '%02x%02x%02x' % color[counter]
        counter += 1
        if (counter % width) != 0:
            file.write("<span style=\"color: #{0}\">{1}</span>".format(color_hex, j))
        else:
            file.write("<br />")
    file.write("""</pre></body>
     </html>""")
    file.close()

def main(video_path):
    config = imgkit.config(wkhtmltoimage='/usr/bin/wkhtmltoimage')
    ascii_string = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@", "&"]
    fps, number_images = video_to_images(video_path)
    os.mkdir('TextImages')

    for i in range(1, number_images + 1):
        image = get_image('Images/Image{0}.jpg'.format(str(i)))
        right_size_image = pixelate_image(image)
        bw_image = grayscale_image(right_size_image)
        converted_list = ascii_conversion(bw_image, ascii_string)
        color_list = get_color(right_size_image)
        print_ascii(converted_list, right_size_image, color_list, i)
        imgkit.from_file('HtmlImages/Html{0}.html'.format(str(i)), 'TextImages/Image{0}.jpg'.format(str(i)), config=config)

    res = Image.open('TextImages/Image1.jpg').size
    video = cv2.VideoWriter('final_video.mp4', cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), int(fps), res)

    for j in range(1, number_images + 1):
        video.write(cv2.imread('TextImages/Image{0}.jpg'.format(str(j))))
    video.release()

    # Clean up folders
    shutil.rmtree('Images')
    shutil.rmtree('HtmlImages')
    shutil.rmtree('TextImages')
    print("✅ Done. Saved to final_video.mp4 and cleaned up folders.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_video>")
    else:
        main(sys.argv[1])
