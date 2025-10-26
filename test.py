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

base_x1, base_x2 = 1048, 1160
region_count = 6
delta_x = -143
delta_y = 248


def ocr_region_test(img, region_coords, region_index=None):
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]

    # 方法1: 欧氏距离法
    target_color1 = (230, 230, 230)
    tolerance1 = 35
    diff1 = np.linalg.norm(roi.astype(np.int16) - np.array(target_color1, dtype=np.int16), axis=2)
    mask1 = (diff1 < tolerance1).astype(np.uint8) * 255
    filtered1 = cv2.bitwise_and(roi, roi, mask=mask1)
    gray1 = cv2.cvtColor(filtered1, cv2.COLOR_BGR2GRAY)
    _, bin_img1 = cv2.threshold(gray1, 10, 255, cv2.THRESH_BINARY)

    # 方法2: RGB区间法
    mask2 = ((roi[:, :, 0] >= 220) & (roi[:, :, 0] <= 255) &
             (roi[:, :, 1] >= 220) & (roi[:, :, 1] <= 255) &
             (roi[:, :, 2] >= 220) & (roi[:, :, 2] <= 255)).astype(np.uint8) * 255
    filtered2 = cv2.bitwise_and(roi, roi, mask=mask2)
    gray2 = cv2.cvtColor(filtered2, cv2.COLOR_BGR2GRAY)
    _, bin_img2 = cv2.threshold(gray2, 10, 255, cv2.THRESH_BINARY)

    # 方法3: 灰度直接阈值
    gray3 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, bin_img3 = cv2.threshold(gray3, 200, 255, cv2.THRESH_BINARY)

    # 方法4: 扩大欧氏距离法
    target_color4 = (240, 240, 240)
    tolerance4 = 60
    diff4 = np.linalg.norm(roi.astype(np.int16) - np.array(target_color4, dtype=np.int16), axis=2)
    mask4 = (diff4 < tolerance4).astype(np.uint8) * 255
    filtered4 = cv2.bitwise_and(roi, roi, mask=mask4)
    gray4 = cv2.cvtColor(filtered4, cv2.COLOR_BGR2GRAY)
    _, bin_img4 = cv2.threshold(gray4, 10, 255, cv2.THRESH_BINARY)

    # 保存中间图
    if region_index is not None:
        cv2.imwrite(f"test_method1_euclidean_{region_index}.png", bin_img1)
        cv2.imwrite(f"test_method2_rgb_range_{region_index}.png", bin_img2)
        cv2.imwrite(f"test_method3_gray_thresh_{region_index}.png", bin_img3)
        cv2.imwrite(f"test_method4_expanded_euclidean_{region_index}.png", bin_img4)

    # 4方法OCR
    res1 = engine(bin_img1, use_cls=False, use_det=False, use_rec=True)
    res2 = engine(bin_img2, use_cls=False, use_det=False, use_rec=True)
    res3 = engine(bin_img3, use_cls=False, use_det=False, use_rec=True)
    res4 = engine(bin_img4, use_cls=False, use_det=False, use_rec=True)
    return [res1, res2, res3, res4]


def detect_purple_y(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"图片未读取成功: {image_path}")
        return None, None, None
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


def process_page_test(image_path, visualize=True):
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

    print("=== 测试不同颜色过滤方法 ===")
    for i in range(region_count):
        dx = delta_x * i
        dy = delta_y * i
        x1 = base_x1 + dx
        x2 = base_x2 + dx
        y1 = y_min + dy
        y2 = y_max + dy
        region = (x1, y1, x2, y2)
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)
        ocr_results = ocr_region_test(img, region, region_index=i + 1)
        result_texts = []
        for idx, res in enumerate(ocr_results, 1):
            ocr_text = ""
            if res and isinstance(res, list):
                texts = [r[1][0] for r in res if len(r) > 1 and r[1]]
                ocr_text = " ".join(texts).strip()
            elif res and hasattr(res, "txts"):
                ocr_text = " ".join(res.txts).strip()
            if not ocr_text:
                ocr_text = "(no text)"
            result_texts.append(f"方法{idx}: {ocr_text}")
        print(f"曲目{i + 1}：" + " | ".join(result_texts))
        # 只显示方法2在图上
        text_pos = (x1, y1 - 10)
        cv2.putText(vis, result_texts[1], text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 2, cv2.LINE_AA)

    if visualize:
        cv2.imwrite("output_test_visualized.jpg", vis)
        print("结果图已保存：output_test_visualized.jpg")
        print("各种预处理方法的图片已保存，文件名格式：test_methodX_xxx_Y.png")


if __name__ == "__main__":
    process_page_test("ADB/SCR/sign11.png", visualize=True)  # 替换为你的大图路径
