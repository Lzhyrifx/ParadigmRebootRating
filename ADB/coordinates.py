import subprocess
import base64
import cv2
import numpy as np
import os
import adbutils

LAST_DEVICE_FILE = ".last_used_device"

def init_device():
    """初始化并选择要连接的设备"""
    try:
        adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
        devices = adb.list()

        if not devices:
            print("没有检测到任何连接的设备，请确保设备已通过ADB连接")
            return None

        # 尝试读取上次使用的设备ID
        last_used_device = None
        if os.path.exists(LAST_DEVICE_FILE):
            with open(LAST_DEVICE_FILE, "r") as f:
                last_used_device = f.read().strip()
                print(f"检测到上次使用的设备：{last_used_device}")

        # 检查上次设备是否仍在连接列表中
        matched_device = None
        if last_used_device:
            for dev in devices:
                if dev.serial == last_used_device:
                    matched_device = dev
                    break

        # 优先使用上次设备（如果存在且仍连接）
        if matched_device:
            print(f"自动连接上次使用的设备：{matched_device.serial}")
            return matched_device.serial

        # 没有上次设备或上次设备已断开，按设备数量处理
        if len(devices) == 1:
            device_id = devices[0].serial
            print(f"只检测到一个设备，自动连接: {device_id}")
        else:
            print("检测到多个设备，请选择要连接的设备：")
            for i, device in enumerate(devices, 1):
                print(f"{i}. {device.serial} (状态: {device.state})")

            while True:
                try:
                    choice = int(input(f"请输入设备编号(1-{len(devices)}): "))
                    if 1 <= choice <= len(devices):
                        device_id = devices[choice - 1].serial
                        break
                    else:
                        print(f"请输入1到{len(devices)}之间的数字")
                except ValueError:
                    print("请输入有效的数字")

        # 保存本次选择的设备ID到文件
        with open(LAST_DEVICE_FILE, "w") as f:
            f.write(device_id)
        print(f"已记住当前设备：{device_id}（下次将自动连接）")

        return device_id

    except ImportError:
        print("请先安装adbutils库：pip install adbutils")
        return None
    except Exception as e:
        print(f"设备连接失败：{str(e)}")
        return None


def take_screenshot_safe(device_id, folder="ADBSCR", filename="screenshot.png"):
    """使用指定设备的ADB截图并安全保存到指定文件夹"""
    try:
        # 确保文件夹存在
        os.makedirs(folder, exist_ok=True)
        full_path = os.path.join(folder, filename)

        # 在指定设备上截图并用base64编码输出
        result = subprocess.run(
            ["adb", "-s", device_id, "shell", "screencap -p | base64"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        # 获取base64字符串（去除换行）
        b64_str = result.stdout.strip()

        # 解码为原始PNG二进制数据
        png_data = base64.b64decode(b64_str)

        # 将二进制数据转换为OpenCV可用的图像格式
        nparr = np.frombuffer(png_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 保存为文件
        with open(full_path, "wb") as f:
            f.write(png_data)

        print(f"✅ 截图已成功保存到 {full_path}")
        return img

    except subprocess.CalledProcessError as e:
        print("❌ ADB命令失败:", e.stderr)
    except Exception as e:
        print("❌ 错误:", str(e))
        print("可能原因：设备未连接、未开启USB调试、adb未安装")
    return None


def get_coordinates(event, x, y, flags, param):
    """鼠标回调函数，用于获取点击的坐标"""
    if event == cv2.EVENT_LBUTTONDOWN:
        scale_factor = param['scale_factor']
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)

        if 0 <= orig_x < param['orig_width'] and 0 <= orig_y < param['orig_height']:
            pixel_color = param['original_image'][orig_y, orig_x]
            b, g, r = pixel_color

            print(f"显示窗口坐标: ({x}, {y})")
            print(f"设备实际坐标: ({orig_x}, {orig_y})")
            print(f"RGB颜色: ({r}, {g}, {b})")
            print(f"BGR颜色: ({b}, {g}, {r})")
            print("-" * 60)

            param['points'].append((orig_x, orig_y))

            # 在显示图像上标记点击位置
            cv2.circle(param['display_img'], (x, y), 5, (0, 0, 255), -1)

            # 显示坐标文本
            text = f"({orig_x},{orig_y})"
            cv2.putText(param['display_img'], text, (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow('设备屏幕 - 点击选择坐标 (q退出, r重置)', param['display_img'])


def main():
    # 1. 选择设备
    print("正在检测连接的设备...")
    device_id = init_device()
    if not device_id:
        print("无法选择设备，程序退出")
        return

    # 2. 使用选定设备获取截图
    print("正在从设备截取屏幕...")
    original_image = take_screenshot_safe(device_id, "ADBSCR", "device_screenshot.png")

    if original_image is None:
        print("无法获取截图，程序退出")
        return

    # 3. 准备显示图像
    img_height, img_width = original_image.shape[:2]
    print(f"设备屏幕尺寸: {img_width} x {img_height}")

    # 计算缩放比例，确保图像适合屏幕显示
    screen_max_width = 1200
    screen_max_height = 800
    scale_factor = min(screen_max_width / img_width, screen_max_height / img_height, 1.0)
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)

    display_img = cv2.resize(original_image, (new_width, new_height))
    print(f"显示尺寸: {new_width} x {new_height}, 缩放比例: {scale_factor:.2f}")
    print("提示: 点击图像选择坐标点，按q退出，按r重置选择，按c查看所有选择的点")

    # 4. 设置OpenCV窗口和回调
    cv2.namedWindow('设备屏幕 - 点击选择坐标 (q退出, r重置)', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('设备屏幕 - 点击选择坐标 (q退出, r重置)', new_width, new_height)

    params = {
        'scale_factor': scale_factor,
        'points': [],
        'display_img': display_img.copy(),
        'original_image': original_image,
        'orig_width': img_width,
        'orig_height': img_height
    }

    cv2.setMouseCallback('设备屏幕 - 点击选择坐标 (q退出, r重置)', get_coordinates, param=params)

    # 5. 主循环
    while True:
        cv2.imshow('设备屏幕 - 点击选择坐标 (q退出, r重置)', params['display_img'])
        key = cv2.waitKey(1) & 0xFF

        # 检查窗口是否关闭
        if cv2.getWindowProperty('设备屏幕 - 点击选择坐标 (q退出, r重置)', cv2.WND_PROP_VISIBLE) < 1:
            break

        # 按q退出
        if key == ord('q'):
            break

        # 按r重置选择
        elif key == ord('r'):
            params['points'] = []
            params['display_img'] = cv2.resize(original_image, (new_width, new_height))
            print("\n已重置所有选择的点")

        # 按c查看所有选择的点
        elif key == ord('c'):
            if params['points']:
                print("\n当前选择的所有坐标点（设备实际坐标）：")
                for i, (x, y) in enumerate(params['points']):
                    print(f"点{i + 1}: ({x}, {y})")
            else:
                print("\n尚未选择任何点")

    cv2.destroyAllWindows()

    # 6. 输出最终选择的坐标（包含设备信息）
    if params['points']:
        print(f"\n\n最终选择的坐标点（设备 {device_id}）：")
        print("=" * 50)
        for i, (x, y) in enumerate(params['points']):
            print(f"点{i + 1}: ({x}, {y})  -->  adb -s {device_id} shell input tap {x} {y}")
        print("=" * 50)
    else:
        print("\n未选择任何坐标点")


if __name__ == "__main__":
    main()