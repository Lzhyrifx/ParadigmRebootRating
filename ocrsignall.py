import cv2
import numpy as np
import logging
import os
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR

logging.getLogger('RapidOCR').disabled = True

engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)

point1 = (1437, 739)
point2 = (1615, 437)
base_box = ((1048, 551), (1158, 623))
region_w = base_box[1][0] - base_box[0][0]
region_h = base_box[1][1] - base_box[0][1]
delta_x = -143
delta_y = 248
region_count = 6

def get_selected_files(folder_path):
    files = []
    png_files = [f for f in os.listdir(folder_path) if f.endswith('.png') and f[:-4].isdigit()]
    if not png_files:
        return files
    max_num = max([int(f[:-4]) for f in png_files])
    idx = 6
    while idx <= max_num:
        fname = f"{idx}.png"
        full_path = os.path.join(folder_path, fname)
        if os.path.exists(full_path):
            files.append(full_path)
        idx += 6
    return files

def detect_purple_y(image_path, save_prefix=None):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_purple = np.array([125, 40, 40])
    upper_purple = np.array([155, 255, 255])
    mask = cv2.inRange(hsv, lower_purple, upper_purple)
    num_samples = max(int(np.hypot(point2[0]-point1[0], point2[1]-point1[1]) / 2), 1)
    xs = np.linspace(point1[0], point2[0], num_samples).astype(int)
    ys = np.linspace(point1[1], point2[1], num_samples).astype(int)
    purple_indices = [i for i, (x, y) in enumerate(zip(xs, ys)) if mask[y, x] > 0]
    if save_prefix:
        overlay = img.copy()
        for (x, y) in zip(xs, ys):
            color = (0, 255, 255) if mask[y, x] > 0 else (128, 128, 128)
            cv2.circle(overlay, (x, y), 2, color, -1)
        cv2.imwrite(f"{save_prefix}_purple.jpg", overlay)
    if not purple_indices:
        return None, mask
    y_mean = int(np.mean([ys[i] for i in purple_indices]))
    return y_mean, mask

def ocr_region(img, region_coords, target_color=(235, 235, 235), tolerance=40, region_index=None, save_prefix=None):
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    diff = np.linalg.norm(roi.astype(np.int16) - np.array(target_color, dtype=np.int16), axis=2)
    mask = (diff < tolerance).astype(np.uint8) * 255
    filtered = cv2.bitwise_and(roi, roi, mask=mask)
    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    _, bin_img = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    if region_index is not None and save_prefix:
        cv2.imwrite(f"{save_prefix}_region{region_index}.jpg", bin_img)
    res = engine(bin_img, use_cls=False, use_det=False, use_rec=True)
    return res

def process_page(image_path, save_dir="sign", visualize=True):
    os.makedirs(save_dir, exist_ok=True)
    img = cv2.imread(image_path)
    basename = os.path.splitext(os.path.basename(image_path))[0]
    save_prefix = os.path.join(save_dir, basename)
    purple_y, _ = detect_purple_y(image_path, save_prefix=save_prefix)
    vis = img.copy()
    if purple_y is None:
        print("未检测到紫色区域")
        return []
    print(f"检测紫色区域平均Y = {purple_y}")
    base_y_offset = purple_y - ((base_box[0][1] + base_box[1][1]) // 2)
    x1_base, y1_base = base_box[0][0], base_box[0][1] + base_y_offset
    x2_base, y2_base = base_box[1][0], base_box[1][1] + base_y_offset
    result_list = []
    for i in range(region_count):
        dx = delta_x * i
        dy = delta_y * i
        x1 = x1_base + dx
        y1 = y1_base + dy
        x2 = x2_base + dx
        y2 = y2_base + dy
        region = (x1, y1, x2, y2)
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)
        res = ocr_region(img, region, region_index=i+1, save_prefix=save_prefix)
        ocr_text = ""
        if res and isinstance(res, list):
            texts = [r[1][0] for r in res if len(r) > 1 and r[1]]
            ocr_text = " ".join(texts).strip()
        elif res and hasattr(res, "txts"):
            ocr_text = " ".join(res.txts).strip()
        if not ocr_text:
            ocr_text = "(no text)"
        print(f"曲目{i+1}：{ocr_text}")
        result_list.append(ocr_text)
    if visualize:
        cv2.imwrite(f"{save_prefix}_visualized.jpg", vis)
    return result_list

if __name__ == "__main__":
    folder = "ADB/SCR"
    selected_files = get_selected_files(folder)
    for file_path in selected_files:
        print("正在处理：", file_path)
        result = process_page(file_path, save_dir="sign", visualize=True)
        print("本图片识别结果：", result)
