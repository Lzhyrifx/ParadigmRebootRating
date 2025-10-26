import cv2
import numpy as np
import logging
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR

logging.getLogger('RapidOCR').disabled = True

engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)


region_count = 6    # 框的数量
delta_x = -143      # 每个框x方向的偏移
delta_y = 248       # 每个框y方向下移
box_w = 112
left_shift = 413



def fill_holes(binary_img):
    # 1. 复制图片，做个边界填充
    h, w = binary_img.shape
    mask = np.zeros((h+2, w+2), np.uint8)
    flood = binary_img.copy()

    # 2. 对边界（左上）floodFill成白色
    cv2.floodFill(flood, mask, (0, 0), 255)
    # 3. flood部分是“外部背景”，原二值的反部分即为内部孔洞
    holes = cv2.bitwise_not(flood)
    # 4. 原图+孔洞，即所有主区域中孔洞全部补白
    filled_img = cv2.bitwise_or(binary_img, holes)
    return filled_img


import os


def ocr_region(
        img, region_coords, region_index=None,
        min_brightness=190, color_similarity=20, size_threshold=80
):
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    # 0. 原始ROI
    os.makedirs("sign", exist_ok=True)
    if region_index is not None:
        cv2.imwrite(f"sign/step0_roi_{region_index}.png", roi)

    cmin = np.min(roi, axis=2)
    cmax = np.max(roi, axis=2)
    mask_brightness = (cmin > min_brightness)
    mask_similarity = (cmax - cmin <= color_similarity)
    mask = (mask_brightness & mask_similarity).astype(np.uint8) * 255
    # 1. 亮度+色纯度mask
    if region_index is not None:
        cv2.imwrite(f"sign/step1_mask_{region_index}.png", mask)

    filtered = cv2.bitwise_and(roi, roi, mask=mask)
    # 2. 过滤后的图像
    if region_index is not None:
        cv2.imwrite(f"sign/step2_filtered_{region_index}.png", filtered)

    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    _, bin_img = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    # 3. 灰度二值结果
    if region_index is not None:
        cv2.imwrite(f"sign/step3_bin_{region_index}.png", bin_img)

    # 4. 闭运算
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    result_img = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel, iterations=1)
    if region_index is not None:
        cv2.imwrite(f"sign/step4_close_{region_index}.png", result_img)

    # 5. 腐蚀
    result_img = cv2.erode(result_img, np.ones((2, 2), np.uint8), iterations=1)
    if region_index is not None:
        cv2.imwrite(f"sign/step5_erode_{region_index}.png", result_img)

    # 6. 去小块
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(result_img, connectivity=8)
    final_img = np.zeros_like(result_img)
    for lbl in range(1, num_labels):
        if stats[lbl, cv2.CC_STAT_AREA] >= size_threshold:
            final_img[labels == lbl] = 255
    if region_index is not None:
        cv2.imwrite(f"sign/step6_area_{region_index}.png", final_img)

    # 7. 最后膨胀
    final_img = cv2.dilate(final_img, np.ones((2, 2), np.uint8), iterations=1)
    if region_index is not None:
        cv2.imwrite(f"sign/step7_dilate_{region_index}.png", final_img)

    # 8. 孔洞填补
    final_img = fill_holes(final_img)
    if region_index is not None:
        cv2.imwrite(f"sign/step8_fillhole_{region_index}.png", final_img)

    # OCR
    res = engine(final_img, use_cls=False, use_det=False, use_rec=True)
    return res


def detect_purple_y(image_path):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_purple = np.array([125, 40, 40])
    upper_purple = np.array([155, 255, 255])
    mask = cv2.inRange(hsv, lower_purple, upper_purple)

    point1 = (1437, 739)
    point2 = (1615, 437)
    num_samples = max(int(np.hypot(point2[0] - point1[0], point2[1] - point1[1]) / 2), 1)
    xs = np.linspace(point1[0], point2[0], num_samples).astype(int)
    ys = np.linspace(point1[1], point2[1], num_samples).astype(int)
    purple_indices = [i for i, (x, y) in enumerate(zip(xs, ys)) if mask[y, x] > 0]

    if not purple_indices:
        return None, mask, None

    y_list = [ys[i] for i in purple_indices]
    y_min = int(np.min(y_list))
    y_max = int(np.max(y_list))
    y_mean = int(np.mean(y_list))

    segments = np.split(purple_indices, np.where(np.diff(purple_indices) > 1)[0] + 1)
    main_segment = max(segments, key=len)
    return (y_min, y_max, y_mean), mask, (
    xs[main_segment[0]], ys[main_segment[0]], xs[main_segment[-1]], ys[main_segment[-1]])


def process_page(image_path, visualize=True):
    img = cv2.imread(image_path)
    purple_info, mask, purple_line = detect_purple_y(image_path)
    if purple_info is None:
        print("未检测到紫色区域")
        return

    y_min, y_max, y_mean = purple_info

    vis = img.copy()


    cv2.line(vis, (1437, 739), (1615, 437), (255, 120, 0), 2)


    if purple_line:
        x_start, y_start, x_end, y_end = purple_line
        cv2.line(vis, (x_start, y_start), (x_end, y_end), (0, 0, 255), 2)


    for i in range(region_count):
        dx = delta_x * i
        dy = delta_y * i

        x1 = base_x1 + dx
        x2 = base_x2 + dx
        y1 = y_min + dy
        y2 = y_max + dy
        region = (x1, y1, x2, y2)
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)  # 黄色
        res = ocr_region(img, region, region_index=i + 1)
        ocr_text = ""
        if res and isinstance(res, list):
            texts = [r[1][0] for r in res if len(r) > 1 and r[1]]
            ocr_text = " ".join(texts).strip()
        elif res and hasattr(res, "txts"):
            ocr_text = " ".join(res.txts).strip()
        if not ocr_text:
            ocr_text = "(no text)"
        print(f"{ocr_text}")
        text_pos = (x1, y1 - 10)
        cv2.putText(vis, ocr_text, text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 2, cv2.LINE_AA)  # 黄色

    if visualize:
        cv2.imwrite("output_visualized.jpg", vis)
        print("结果图已保存：output_visualized.jpg")


if __name__ == "__main__":
    process_page("ADB/SCR/sign1.PNG", visualize=True)
