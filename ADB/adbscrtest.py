import uiautomator2 as u2
import time
import os
import cv2
import re
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

# 歌曲坐标列表
song_coords = [
    (1172, 579),
    (1025, 833),
    (881, 1081),
    (744, 1326),
    (603, 1577),
    (464, 1818),
]

# 截图保存目录
screenshot_dir = "Temp/"
# 等级检测区域坐标
region_song_level = (667, 1786, 827, 1871)
# 指定的最低可接受等级（可根据需要修改）
MIN_ACCEPTABLE_LEVEL = "14+"  # 例如："13", "13+", "14", "14+"等

# 计数器初始化
counter = 1
# 控制是否继续截图的标志
continue_screenshot = True


def parse_level(level_str):
    """解析等级字符串为可比较的数值"""
    if not level_str:
        return (0, False)

    # 提取数字和是否带+号
    match = re.match(r'^(\d+)(\+?)$', level_str.strip())
    if match:
        number = int(match.group(1))
        has_plus = bool(match.group(2))
        return (number, has_plus)
    return (0, False)  # 无法解析的情况


def ocr_region(image_path, region_coords):
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    res = engine(roi, use_cls=False, use_det=False, use_rec=True)
    return res



def process_songs(d):
    """处理一组歌曲（6首）的截图"""
    global counter, continue_screenshot

    for idx, (x, y) in enumerate(song_coords):
        if not continue_screenshot:
            break

        print(f"\n处理歌曲：{counter}")
        tap_coordinate(d, x, y)
        take_screenshot(d, str(counter))

        # 每6首歌检测一次等级
        if (counter % 6 == 0):
            print(f"检测第{counter}首歌的等级...")
            image_path = os.path.join(screenshot_dir, f"{counter}.png")
            level_strxxx = ocr_region(image_path, region_song_level)
            level_str = level_strxxx.txts[0]
            print(f"检测到等级: {level_str}")

            # 解析等级并比较
            current_level = parse_level(level_str)
            min_level = parse_level(MIN_ACCEPTABLE_LEVEL)

            if current_level < min_level:
                print(f"等级{level_str}低于指定等级{MIN_ACCEPTABLE_LEVEL}，停止截图")
                continue_screenshot = False
                break

        counter += 1


def slide(d):
    """滑动屏幕到下一页"""
    w = d.info['displayWidth']
    x = w * 0.5
    start_y = 1800
    end_y = 1100

    # 第一次滑动
    d.touch.down(x, start_y)
    time.sleep(0.01)
    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.1)
    d.touch.up(x, end_y)

    # 第二次滑动
    d.touch.down(x, start_y)
    time.sleep(0.01)
    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.4)


def init_device():
    """初始化设备连接"""
    try:
        d = u2.connect()
        print(f"设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
        return d
    except Exception as e:
        print(f"设备连接失败：{str(e)}")
        exit(1)


def tap_coordinate(d, x, y):
    """点击指定坐标"""
    try:
        d.click(x, y)
        print(f"已点击坐标：({x}, {y})")
        time.sleep(0.5)  # 点击后等待界面响应
    except Exception as e:
        print(f"点击失败：{str(e)}")


def take_screenshot(d, song_name):
    """截取当前屏幕并保存"""
    local_path = os.path.join(screenshot_dir, f"{song_name}.png")
    try:
        success = d.screenshot(local_path)
        if success and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            print(f"已保存截图：{local_path}")
        else:
            print(f"截图保存失败：{local_path}")
    except Exception as e:
        print(f"截图失败：{str(e)}")
    time.sleep(0.5)  # 截图后等待


if __name__ == "__main__":
    d = init_device()
    os.makedirs(screenshot_dir, exist_ok=True)

    start_time = time.time()

    # 验证最低等级设置是否有效
    if parse_level(MIN_ACCEPTABLE_LEVEL) == (0, False):
        print(f"错误：无效的最低等级设置 {MIN_ACCEPTABLE_LEVEL}")
        print("请使用正确的等级格式，如：13, 13+, 14, 14+等")
        exit(1)

    # 循环处理，直到需要停止
    while continue_screenshot:
        process_songs(d)
        if continue_screenshot:  # 如果还需要继续，才滑动到下一页
            slide(d)

    elapsed_time = time.time() - start_time
    total_songs = counter - 1  # 减去初始的1
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    if total_songs > 0:
        print(f"平均每首歌耗时: {elapsed_time / total_songs:.2f} 秒")
    print(f"共处理 {total_songs} 首歌")
    print("=" * 50)
