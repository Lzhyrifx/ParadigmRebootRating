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
    end_y = 843

    slide(x, start_y, end_y)

    d.click(x, h)

    slide(x, start_y, end_y)

    d.click(x, h)

def reset_slide():
    x = w * 0.5
    start_y = 100
    end_y = 1800

    slide(x, start_y, end_y)
    time.sleep(0.2)
    slide(x, start_y, end_y)
    time.sleep(0.2)
    d.click(x, h)

def screenshot(d, temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    local_path = os.path.join(temp_dir, "Temp.png")
    try:
        d.screenshot(local_path)
        if os.path.exists(local_path):
            print(f"已保存截图：{local_path}")
            return local_path
        else:
            print(f"截图文件未生成：{local_path}")
            return None
    except Exception as e:
        print(f"截图失败：{str(e)}")
        return None

previous_song = None
temp_dir = "Temp/"
d = init_device()
w = d.info['displayWidth']
h = d.info['displayHeight'] * 0.5
reset_region = (1316,712,1439,787)
reset_point = (80,1065)
top_region = (937, 448, 1537, 525)

previous = None


while True:
    image_path = screenshot(d, temp_dir)
    ocr_result = ocr_region(image_path,reset_region)
    if ocr_result.txts:
        random_level = ocr_result.txts[0].replace("t", "+").strip()
        print(f"识别等级: {random_level}")

        if random_level in ["16", "16+", "17"]:
            print(f"检测到符合条件的等级: {random_level}")
            break
        else:
            print(f"等级 {random_level} 不符合条件，继续检测...")
    d.click(*reset_point)
    time.sleep(0.5)


while True:
    reset_slide()
    time.sleep(0.1)

    image_path = screenshot(d, temp_dir)
    ocr_result = ocr_region(image_path, top_region)
    current = ocr_result.txts[0].strip() if ocr_result.txts else ""

    if not current:
        print("未识别到文本，重试")

        continue

    print(f"识别到: {current}")

    if previous is not None:
        if current == previous:
            print("TOP")
            break
    previous = current

while True:
    scroll()
    time.sleep(3)

