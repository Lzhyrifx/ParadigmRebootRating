import os

import uiautomator2 as u2
import time
from function import init_device, ocr_region, screenshot

d = init_device()
w = d.info['displayWidth']
h = d.info['displayHeight'] * 0.5
reset_region = (947,448,1535,520)
random_region = (1314,710,1444,782)
temp_dir = "Temp/"


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







screenshot(d, temp_dir)
image_path = os.path.join(temp_dir)

level_str = ocr_region(reset_region, image_path).txts[0]
print(level_str)


reset()
scroll()
time.sleep(1)
scroll()
time.sleep(1)
scroll()
time.sleep(1)
scroll()