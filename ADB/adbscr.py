import re
import signal
import time
import os
import cv2
import numpy as np
from function import ocr_region, init_device

song_coords = [
    (1110, 491),
    (1014, 744),
    (862, 1003),
    (728, 1230),
    (584, 1468),
    (427, 1735),
]

temp_dir = "Temp"
screenshot_dir = "SCR/"
MIN_ACCEPTABLE_LEVEL = "16"
region_song_level = (2587, 1636, 2838, 1764)
reset_region = (1316, 712, 1439, 787)
reset_point = (80, 1065)
top_region = (937, 448, 1537, 525)
sign_counter = 1

point1 = (1437, 739)
point2 = (1615, 437)
reference_point = (1526, 588)
y_threshold = 30


def signal_handler():
    global continue_screenshot, is_saving_screenshot
    print("\n收到停止信号，等待当前截图完成后退出")
    continue_screenshot = False
    wait_start = time.time()
    while is_saving_screenshot and (time.time() - wait_start < 2):
        time.sleep(0.1)
    print("程序已安全退出")
    exit(0)


def parse_level(level_str):
    if not level_str:
        return 0, False
    match = re.match(r'^(\d+)(\+?)$', level_str.strip())
    if match:
        number = int(match.group(1))
        has_plus = bool(match.group(2))
        return number, has_plus
    return 0, False


def slide(x, start_y, end_y):
    d.touch.down(x, start_y)
    for i in range(1, 11):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
    d.touch.up(x, end_y)


def re_slide(start_xy, end_xy, steps=10):
    sx, sy = int(start_xy[0]), int(start_xy[1])
    ex, ey = int(end_xy[0]), int(end_xy[1])
    d.touch.down(sx, sy)
    for i in range(1, steps + 1):
        x = int(sx + (ex - sx) * i / steps)
        y = int(sy + (ey - sy) * i / steps)
        d.touch.move(x, y)
    d.touch.up(ex, ey)
    d.click(cx, cy)


def temp_screenshot(d, temp_dir):
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


def screenshot(d, song_name):
    global is_saving_screenshot
    local_path = os.path.join(screenshot_dir, f"{song_name}.png")
    try:
        is_saving_screenshot = True
        d.screenshot(local_path)
        print(f"已保存截图：{local_path}")
    except Exception as e:
        print(f"截图失败：{str(e)}")
    finally:
        is_saving_screenshot = False
    return local_path


def reset_slide(count=2):
    x = w * 0.5
    start_y = 100
    end_y = 1800
    for _ in range(count):
        slide(x, start_y, end_y)
        time.sleep(0.2)
    d.click(x, h)



def re_center():
    img_path = temp_screenshot(d, temp_dir)
    img = cv2.imread(img_path)
    if img is None:
        print(f"无法读取图像：{img_path}")
        return


    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_purple = np.array([125, 40, 40])
    upper_purple = np.array([155, 255, 255])
    mask = cv2.inRange(hsv, lower_purple, upper_purple)


    num_samples = max(int(np.hypot(point2[0]-point1[0], point2[1]-point1[1]) / 2), 1)
    xs = np.linspace(point1[0], point2[0], num_samples).astype(int)
    ys = np.linspace(point1[1], point2[1], num_samples).astype(int)
    purple_indices = [i for i, (x, y) in enumerate(zip(xs, ys)) if mask[y, x] > 0]

    # vis = img.copy()
    # cv2.line(vis, point1, point2, (0, 255, 0), 2)

    if purple_indices:

        segments = np.split(purple_indices, np.where(np.diff(purple_indices) > 1)[0] + 1)
        main_segment = max(segments, key=len)
        start_i, end_i = main_segment[0], main_segment[-1]
        mid_i = (start_i + end_i) // 2
        mid_x, mid_y = int(xs[mid_i]), int(ys[mid_i])

        y_distance = mid_y - reference_point[1]
        print(f"\n检测到紫色中心：({mid_x}, {mid_y})")
        print(f"与参考点 {reference_point} 的y轴偏差：{y_distance}")


        if abs(y_distance) > y_threshold:
            if y_distance > 0:
                print("检测到偏下,向上滑动回正")
                slide_scale = 1.7
            else:
                print("检测到偏上,向下滑动回正")
                slide_scale = 1.2

            delta_y = reference_point[1] - mid_y
            end_y = int(mid_y + delta_y * slide_scale)
            print(f"执行回正：({mid_x}, {mid_y}) → ({mid_x}, {end_y})")
            re_slide( (mid_x, mid_y), (mid_x, end_y))

        # cv2.circle(vis, (mid_x, mid_y), 4, (0, 0, 255), -1)
        # cv2.circle(vis, reference_point, 4, (255, 0, 0), -1)
        # cv2.line(vis, (mid_x, mid_y), reference_point, (255, 255, 0), 1)
    else:
        print("未检测到紫色区域")

    #cv2.imwrite("center.png", vis)
    #print("检测结果已保存:center.png\n")



def scroll(frequency=1):
    x = w * 0.5
    start_y = 1800
    end_y = 836
    slide(x, start_y, end_y)
    d.click(x, h)
    slide(x, start_y, end_y)
    d.click(x, h)

    global scroll_counter
    scroll_counter += 1
    if scroll_counter % frequency == 0:
        re_center()


def read_songs(d):
    global counter, continue_screenshot
    for idx, (x, y) in enumerate(song_coords):
        if not continue_screenshot:
            break
        print(f"\n处理歌曲：{counter}")
        d.click(x, y)
        image_path = screenshot(d, str(counter))
        if counter % 6 == 0:
            print(f"检测第{counter}首歌的等级...")
            level_str = ocr_region(image_path, region_song_level).txts[0]
            level_str = level_str.replace("t", "+")
            print(f"检测到等级: {level_str}")
            current_level = parse_level(level_str)
            min_level = parse_level(MIN_ACCEPTABLE_LEVEL)
            if current_level < min_level:
                print(f"等级{level_str}低于指定等级{MIN_ACCEPTABLE_LEVEL}，停止截图")
                continue_screenshot = False
                break
        counter += 1


d = init_device()
w = d.info['displayWidth']
h = d.info['displayHeight'] * 0.5
cx = d.info['displayWidth'] * 0.5
cy = d.info['displayHeight'] * 0.5

continue_screenshot = True
is_saving_screenshot = False
counter = 1
scroll_counter = 0
previous = None
os.makedirs(screenshot_dir, exist_ok=True)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    image_path = temp_screenshot(d, temp_dir)
    ocr_result = ocr_region(image_path, top_region)
    top1 = ocr_result.txts[0].strip() if ocr_result.txts else ""
    if not top1:
        print("未识别到文本，重试")
    else:
        print(f"识别到: {top1}")


    reset_slide(1)


    image_path = temp_screenshot(d, temp_dir)
    ocr_result = ocr_region(image_path, top_region)
    top2 = ocr_result.txts[0].strip() if ocr_result.txts else ""
    if not top2:
        print("未识别到文本，重试")
    else:
        print(f"识别到: {top2}")

    TOP = 0

    if top1 and top2 and top1 == top2:
        print("检测到已经在最顶端")
        TOP = 1
    else:
        print("尚未在最顶端，准备执行滑动操作")

    while TOP == 0:
        image_path = temp_screenshot(d, temp_dir)
        ocr_result = ocr_region(image_path, reset_region)
        if ocr_result.txts:
            random_level = ocr_result.txts[0].replace("t", "+").strip()
            print(f"识别等级: {random_level}")
            if random_level in ["16", "16+", "17"]:
                print(f"检测到符合条件的等级: {random_level}")
                break
            else:
                print(f"等级 {random_level} 不符合条件，继续检测")
        d.click(*reset_point)
        time.sleep(0.5)

    while TOP == 0:
        reset_slide()
        time.sleep(0.1)
        image_path = temp_screenshot(d, temp_dir)
        ocr_result = ocr_region(image_path, top_region)
        current = ocr_result.txts[0].strip() if ocr_result.txts else ""
        if not current:
            print("未识别到文本，重试")
            continue
        print(f"识别到: {current}")
        if previous is not None and current == previous:
            print("TOP")
            break
        previous = current

    start_time = time.time()
    while continue_screenshot:
        read_songs(d)
        if continue_screenshot:
            scroll()
            sign_path = os.path.join(screenshot_dir, f"sign{sign_counter}.png")
            d.screenshot(sign_path)
            sign_counter += 1

    elapsed_time = time.time() - start_time
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / (counter - 1):.2f} 秒")

