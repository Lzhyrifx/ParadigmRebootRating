import os

import uiautomator2 as u2
import time
from function import init_device, ocr_region, screenshot

d = init_device()
w = d.info['displayWidth']
h = d.info['displayHeight'] * 0.5
reset_region = (947,448,1535,520)

def slide(x,start_y,end_y):
    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)

    d.touch.up(x, end_y)

def scroll():

    x = w * 0.5
    start_y = 1800
    end_y = 843

    slide(x, start_y, end_y)

    d.click(x, h)

    slide(x, start_y, end_y)

    d.click(x, h)

def reset():
    x = w * 0.5

    start_y = 100
    end_y = 1800


    slide(x, start_y, end_y)
    time.sleep(0.2)
    slide(x, start_y, end_y)

    time.sleep(0.2)


temp_dir = "Temp/"
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

screenshot(d, temp_dir)

image_path = os.path.join(temp_dir, "screenshot.png")

random_level = ocr_region(reset_region, image_path).txts[0]
random_level = random_level.replace("t", "+")
if random_level != "16" or "16+" or "17"
    d.click()

reset()
scroll()
time.sleep(1)
scroll()
time.sleep(1)
scroll()
time.sleep(1)
scroll()