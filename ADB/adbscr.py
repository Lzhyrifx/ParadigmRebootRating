import re
import signal
import time
import os
from function import ocr_region,init_device


song_coords = [
    (1110, 491),
    (1014, 744),
    (862, 1003),
    (728, 1230),
    (584, 1468),
    (427, 1735),
]

screenshot_dir = "SCR/"
continue_screenshot = True
MIN_ACCEPTABLE_LEVEL = "16"
region_song_level = (2587, 1636, 2838, 1764)
counter = 1
is_saving_screenshot = False

def signal_handler(signum, frame):

    global continue_screenshot, is_saving_screenshot
    print("\n收到停止信号，等待当前截图完成后退出...")
    continue_screenshot = False


    wait_start = time.time()
    while is_saving_screenshot and (time.time() - wait_start < 3):
        time.sleep(0.1)

    if is_saving_screenshot:
        print("截图操作超时，强制退出")
    else:
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


def slide(d):
    global continue_screenshot
    if not continue_screenshot:
        return
    w = d.info['displayWidth']
    x = w * 0.5
    start_y = 1800
    end_y = 707

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
    d.touch.up(x, end_y)




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
        if not continue_screenshot:
            break

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    d = init_device()
    os.makedirs(screenshot_dir, exist_ok=True)

    start_time = time.time()

    while continue_screenshot:
        read_songs(d)
        if continue_screenshot:
            slide(d)


    elapsed_time = time.time() - start_time
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / (counter - 1):.2f} 秒")
    print("=" * 50)
    print("启动OCR")