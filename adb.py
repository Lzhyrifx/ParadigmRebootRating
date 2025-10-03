import cv2
import numpy as np
import subprocess
import time
from paddleocr import PaddleOCR

# 初始化 OCR（首次运行会自动下载模型）
ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # lang='en' 为英文


def adb_screencap():
    """通过 ADB 获取屏幕截图，返回 OpenCV 图像"""
    result = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError("ADB 截图失败")

    # 修复 Windows 下 PNG 换行符问题（adb exec-out 在 Windows 可能损坏 PNG）
    img_bytes = result.stdout.replace(b'\r\n', b'\n')
    img_array = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img


def crop_region(img, x1, y1, x2, y2):
    """裁剪指定区域 (x1,y1) 到 (x2,y2)"""
    return img[y1:y2, x1:x2]


def ocr_region(img):
    """对图像进行 OCR，返回识别文本（拼接所有行）"""
    result = ocr.ocr(img, cls=True)
    if not result or not result[0]:
        return ""

    texts = [line[1][0] for line in result[0]]  # 提取文本
    return "".join(texts).replace(" ", "")


def adb_tap(x, y):
    """ADB 点击坐标"""
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])


def adb_swipe(x1, y1, x2, y2, duration=300):
    """ADB 滑动"""
    subprocess.run(["adb", "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])


# ================== 主逻辑 ==================
def main():
    # 定义要 OCR 的区域（根据你的平板分辨率调整！）
    # 例如：识别屏幕顶部状态栏的“电量”或“Wi-Fi”图标附近文字
    OCR_REGION = (100, 50, 400, 100)  # (x1, y1, x2, y2)

    while True:
        try:
            # 1. 截图
            screen = adb_screencap()

            # 2. 裁剪 OCR 区域
            roi = crop_region(screen, *OCR_REGION)

            # （可选）保存调试图
            # cv2.imwrite("debug_roi.png", roi)

            # 3. OCR 识别
            text = ocr_region(roi)
            print(f"识别结果: '{text}'")

            # 4. 根据文本执行操作
            if "登录" in text:
                print("检测到登录按钮，点击！")
                adb_tap(300, 800)  # 假设登录按钮坐标
            elif "错误" in text:
                print("检测到错误，返回上一页")
                adb_tap(50, 100)  # 返回键坐标
            elif "完成" in text:
                print("任务完成，退出")
                break

            time.sleep(2)  # 避免频繁截图（根据需求调整）

        except KeyboardInterrupt:
            print("用户中断")
            break
        except Exception as e:
            print("发生错误:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()