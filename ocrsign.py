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


point1 = (1437, 739)
point2 = (1615, 437)


base_box = ((1048, 551), (1158, 623))
region_w = base_box[1][0] - base_box[0][0]
region_h = base_box[1][1] - base_box[0][1]

delta_x = -143
delta_y = 248
region_count = 6



def detect_purple_y(image_path):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_purple = np.array([125, 40, 40])
    upper_purple = np.array([155, 255, 255])
    mask = cv2.inRange(hsv, lower_purple, upper_purple)

    num_samples = max(int(np.hypot(point2[0]-point1[0], point2[1]-point1[1]) / 2), 1)
    xs = np.linspace(point1[0], point2[0], num_samples).astype(int)
    ys = np.linspace(point1[1], point2[1], num_samples).astype(int)
    purple_indices = [i for i, (x, y) in enumerate(zip(xs, ys)) if mask[y, x] > 0]

    if not purple_indices:
        return None, mask

    y_mean = int(np.mean([ys[i] for i in purple_indices]))
    return y_mean, mask



def ocr_region(img, region_coords, target_color=(235, 235, 235), tolerance=35,region_index=None):
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    diff = np.linalg.norm(roi.astype(np.int16) - np.array(target_color, dtype=np.int16), axis=2)
    mask = (diff < tolerance).astype(np.uint8) * 255
    filtered = cv2.bitwise_and(roi, roi, mask=mask)
    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    _, bin_img = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)


    if region_index is not None:
        cv2.imwrite(f"debug_ocr_input_region_{region_index}.jpg", bin_img)

    res = engine(bin_img, use_cls=False, use_det=False, use_rec=True)
    return res



def process_page(image_path, visualize=True):
    img = cv2.imread(image_path)
    purple_y, _ = detect_purple_y(image_path)
    vis = img.copy()

    if purple_y is None:
        print("未检测到紫色区域")
        return

    print(f"检测紫色区域平均Y = {purple_y}")


    base_y_offset = purple_y - ((base_box[0][1] + base_box[1][1]) // 2)
    x1_base, y1_base = base_box[0][0], base_box[0][1] + base_y_offset
    x2_base, y2_base = base_box[1][0], base_box[1][1] + base_y_offset


    for i in range(region_count):

        dx = delta_x * i
        dy = delta_y * i
        x1 = x1_base + dx
        y1 = y1_base + dy
        x2 = x2_base + dx
        y2 = y2_base + dy
        region = (x1, y1, x2, y2)


        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)

        res = ocr_region(img, region,region_index=i+1)
        ocr_text = ""
        if res and isinstance(res, list):
            texts = [r[1][0] for r in res if len(r) > 1 and r[1]]
            ocr_text = " ".join(texts).strip()
        elif res and hasattr(res, "txts"):
            ocr_text = " ".join(res.txts).strip()
        if not ocr_text:
            ocr_text = "(no text)"

        print(f"曲目{i+1}：{ocr_text}")


        text_pos = (x1, y1 - 10)
        cv2.putText(vis, ocr_text, text_pos,
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 2, cv2.LINE_AA)

    if visualize:
        cv2.imwrite("output_visualized.jpg", vis)
        print("结果图已保存：output_visualized.jpg")


if __name__ == "__main__":
    process_page("SCR/sign.jpg", visualize=True)
