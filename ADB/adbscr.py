import uiautomator2 as u2
import time
import os


song_coords = [
    (1172, 579),
    (1025, 833),
    (881, 1081),
    (744, 1326),
    (603, 1577),
    (464, 1818),
]

screenshot_dir = "Temp/"


counter = 1

d = u2.connect()
w = d.info['displayWidth']
x = w * 0.5
start_y = 1800
end_y = 1100

def scr():
    global counter
    for idx, (x, y) in enumerate(song_coords):
        print(f"\n处理歌曲：{counter}")

        tap_coordinate(d, x, y)
        take_screenshot(d, str(counter))
        counter += 1


def slide():
    prr_swipe()
    prr_swipe()

def prr_swipe():
    d.touch.down(x, start_y)
    time.sleep(0.01)
    for i in range(1, 16):
        y = start_y + (end_y - start_y) * i / 10
        d.touch.move(x, y)
        time.sleep(0.001)
    time.sleep(0.6)
    d.touch.up(x, end_y)


def init_device():
    try:
        d = u2.connect()

        print(f"设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
        return d
    except Exception as e:
        exit(1)


def tap_coordinate(d, x, y):
    try:
        d.click(x, y)

        print(f"已点击坐标：({x}, {y})")
    except Exception as e:
        print(f"点击失败：{str(e)}")


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



if __name__ == "__main__":
    d = init_device()
    os.makedirs(screenshot_dir, exist_ok=True)

    start_time = time.time()
    loop_count = 10
    for i in range(loop_count):
        scr()
        if i < loop_count - 1:
            slide()


    elapsed_time = time.time - start_time
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / (counter - 1):.2f} 秒")
    print("=" * 50)
    print("启动OCR")