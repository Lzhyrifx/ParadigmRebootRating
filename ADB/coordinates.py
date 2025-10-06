import subprocess
import base64
import cv2
import numpy as np
import os  # 新增：用于文件夹操作


def take_screenshot_safe(folder="ADBSCR", filename="screenshot.png"):
    """使用ADB从设备截图并安全保存到指定文件夹"""
    try:
        # 确保文件夹存在
        os.makedirs(folder, exist_ok=True)
        full_path = os.path.join(folder, filename)

        # 在设备上截图并用base64编码输出（避免二进制传输问题）
        result = subprocess.run(
            ["adb", "shell", "screencap -p | base64"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # 此时输出是文本（base64字符串）
            check=True
        )

        # 获取base64字符串（可能包含换行，需去除）
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
            print(f"设备实际坐标: ({orig_x}, {orig_y})")  # 这是设备上的实际坐标，可用于ADB点击
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
    # 1. 使用ADB获取设备截图，保存到ADBSCR文件夹
    print("正在从设备截取屏幕...")
    original_image = take_screenshot_safe("ADBSCR", "device_screenshot.png")

    if original_image is None:
        print("无法获取截图，程序退出")
        return

    # 2. 准备显示图像
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

    # 3. 设置OpenCV窗口和回调
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

    # 4. 主循环
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

    # 5. 输出最终选择的坐标
    if params['points']:
        print("\n\n最终选择的坐标点（可直接用于ADB点击命令）：")
        print("=" * 50)
        for i, (x, y) in enumerate(params['points']):
            print(f"点{i + 1}: ({x}, {y})  -->  adb shell input tap {x} {y}")
        print("=" * 50)
    else:
        print("\n未选择任何坐标点")


if __name__ == "__main__":
    main()
