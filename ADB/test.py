import uiautomator2 as u2
import time
import os
import threading

# 歌曲坐标
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


# 滑动参数
def init_slide_params(d):
    w = d.info['displayWidth']
    h = d.info['displayHeight']
    # 基于屏幕比例计算，适应不同设备
    return {
        'x': w * 0.5,
        'start_y': h * 0.85,  # 屏幕底部85%位置
        'end_y': h * 0.45  # 屏幕底部45%位置
    }


slide_params = None


def scr(d):
    global counter
    for idx, (x, y) in enumerate(song_coords):
        print(f"\n处理歌曲：{counter}")

        # 移除不支持的duration参数
        d.click(x, y)  # 普通点击，不指定duration

        # 启动线程异步截图，不阻塞主流程
        threading.Thread(target=take_screenshot, args=(d, str(counter))).start()

        counter += 1
        # 仅保留必要的等待时间，根据实际应用响应调整
        time.sleep(0.3)


def slide(d):
    # 优化滑动操作，使用更高效的实现
    d.swipe(
        slide_params['x'],
        slide_params['start_y'],
        slide_params['x'],
        slide_params['end_y'],
        duration=0.2  # swipe方法支持duration参数
    )
    # 滑动后仅保留必要的等待
    time.sleep(0.5)


def init_device():
    try:
        # 优化连接方式，使用adb连接可能更快
        d = u2.connect()  # 可以尝试使用u2.connect_usb()直接连接USB设备

        # 关闭动画以提高操作速度
        d.shell("settings put global window_animation_scale 0.0")
        d.shell("settings put global transition_animation_scale 0.0")
        d.shell("settings put global animator_duration_scale 0.0")

        print(f"设备连接成功：{d.device_info['model']}（Android {d.device_info['version']}）")
        return d
    except Exception as e:
        print(f"设备连接失败：{str(e)}")
        exit(1)


def tap_coordinate(d, x, y):
    try:
        # 移除不支持的duration参数
        d.click(x, y)
        print(f"已点击坐标：({x}, {y})")
    except Exception as e:
        print(f"点击失败：{str(e)}")


def take_screenshot(d, song_name):
    local_path = os.path.join(screenshot_dir, f"{song_name}.png")
    try:
        # 使用压缩格式和更低质量截图（如果应用允许）
        success = d.screenshot(local_path, quality=80)  # 降低截图质量
        if success and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            print(f"已保存截图：{local_path}")
        else:
            print(f"截图保存可能不完整：{local_path}")
    except Exception as e:
        print(f"截图失败：{str(e)}")


if __name__ == "__main__":
    d = init_device()
    slide_params = init_slide_params(d)
    os.makedirs(screenshot_dir, exist_ok=True)

    start_time = time.time()
    loop_count = 10

    for i in range(loop_count):
        scr(d)
        if i < loop_count - 1:
            slide(d)

    # 等待可能还在运行的截图线程
    time.sleep(1)

    elapsed_time = time.time() - start_time
    print(f"\n" + "=" * 50)
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每首歌耗时: {elapsed_time / (counter - 1):.2f} 秒")
    print("=" * 50)
    print("启动OCR")
