import os

import time
from function import init_device, ocr_region



def slide(x,start_y,end_y):
    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)

    d.touch.up(x, end_y)

def scroll():

    x = w * 0.5
    start_y = 1800
    end_y = 880

    d.swipe(x, start_y, x,end_y,duration=0.1)
    d.click(x, h)

    d.swipe(x, start_y, x,end_y,duration=0.1)

    d.click(x, h)

def reset():
    x = w * 0.5

    start_y = 100
    end_y = 1800


    slide(x, start_y, end_y)
    time.sleep(0.2)
    slide(x, start_y, end_y)

    time.sleep(0.2)

def screenshot(d,temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    local_path = os.path.join(temp_dir, f"Temp.png")
    try:
        d.screenshot(local_path)
        print(f"已保存截图：{local_path}")
    except Exception as e:
        print(f"截图失败：{str(e)}")
    return local_path

temp_dir = "Temp/"
d = init_device()
w = d.info['displayWidth']
h = d.info['displayHeight'] * 0.5
reset_region = (947,448,1535,520)


d.click(427, 1735)
time.sleep(1)
image_path = screenshot(d,temp_dir)


