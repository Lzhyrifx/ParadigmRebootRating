import os
import cv2
from pathlib import Path


def classify_screenshot_fast(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return "读取失败"

    # 获取左下角像素颜色
    height, width = img.shape[:2]
    x, y = 27, 1934
    b, g, r = img[y, x]
    print(b, g, r)
    return "type1" if (60 <= r <= 66 and 136 <= g <= 142 and 170 <= b <= 176) else "type2"


# 预计结果：总耗时约0.1-0.2秒，平均每张0.1-0.2ms

img = "SCR/SOC.jpg"
folder_path = "SRC"
image_path = Path(folder_path)


# 快速遍历和分类
src_folder = "SCR"

for filename in os.listdir(src_folder):
    if filename.upper().endswith('.JPG'):
        img_path = os.path.join(src_folder, filename)

        # 直接传递图像路径给函数
        result = classify_screenshot_fast(img_path)
        print(f"{filename}: {result}")