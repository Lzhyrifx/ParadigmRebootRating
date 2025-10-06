import re

import cv2
import uiautomator2 as u2
import time
import os
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import logging
# 配置日志，禁用RapidOCR的日志输出
logging.getLogger('RapidOCR').disabled = True

# 初始化OCR引擎
engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)

song_coords = [
    (1110, 491),
    (1014, 744),
    (862, 1003),
    (728, 1230),
    (584, 1468),
    (427, 1735),
]

screenshot_dir = "Temp/"
continue_screenshot = True
MIN_ACCEPTABLE_LEVEL = "16+"
region_song_level = (2587, 1636, 2838, 1764)
counter = 1

d = u2.connect()


def parse_level(level_str):
    """解析等级字符串为可比较的数值"""
    if not level_str:
        return (0, False)

    # 提取数字和是否带+号
    match = re.match(r'^(\d+)(\+?)$', level_str.strip())
    if match:
        number = int(match.group(1))
        has_plus = bool(match.group(2))
        return number, has_plus
    return 0, False  # 无法解析的情况


def ocr_region(image_path, region_coords):
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    res = engine(roi, use_cls=False, use_det=False, use_rec=True)
    return res


def scr():
    global counter
    for idx, (x, y) in enumerate(song_coords):
        print(f"\n处理歌曲：{counter}")

        d.click(x, y)
        take_screenshot(d, str(counter))
        counter += 1


def slide(d):
    w = d.info['displayWidth']
    x = w * 0.5
    start_y = 1800
    end_y = 705

    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.2)
    d.touch.up(x, end_y)


    d.touch.down(x, start_y)

    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.6)


def init_device():
    try:
        d = u2.connect()

        print(f"设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
        return d
    except Exception as e:
        exit(1)


def take_screenshot(d, song_name):
    local_path = os.path.join(screenshot_dir, f"{song_name}.png")
    try:
        success = d.screenshot(local_path)
        if success and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            print(f"已保存截图：{local_path}")
        else:
            print(f"已保存截图：{local_path}")
    except Exception as e:
        print(f"截图失败：{str(e)}")


def process_songs(d):

    global counter, continue_screenshot

    for idx, (x, y) in enumerate(song_coords):
        if not continue_screenshot:
            break

        print(f"\n处理歌曲：{counter}")
        d.click(x, y)
        take_screenshot(d, str(counter))

        # 每6首歌检测一次等级
        if counter % 6 == 0:
            print(f"检测第{counter}首歌的等级...")
            image_path = os.path.join(screenshot_dir, f"{counter}.png")
            level_str = ocr_region(image_path, region_song_level).txts[0]
            level_str = level_str.replace("t", "+")
            print(f"检测到等级: {level_str}")

            # 解析等级并比较
            current_level = parse_level(level_str)
            min_level = parse_level(MIN_ACCEPTABLE_LEVEL)

            if current_level < min_level:
                print(f"等级{level_str}低于指定等级{MIN_ACCEPTABLE_LEVEL}，停止截图")
                continue_screenshot = False
                break

        counter += 1

if __name__ == "__main__":
    d = init_device()
    os.makedirs(screenshot_dir, exist_ok=True)

    start_time = time.time()

    while continue_screenshot:
        process_songs(d)
        if continue_screenshot:
            slide(d)


    elapsed_time = time.time() - start_time
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / (counter - 1):.2f} 秒")
    print("=" * 50)
    print("启动OCR")