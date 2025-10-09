import cv2
from rapidfuzz import fuzz, process
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import logging

logging.getLogger('RapidOCR').disabled = True

engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)

def ocr_region(image_path, region_coords):
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    res = engine(roi, use_cls=False, use_det=False, use_rec=True)
    return res

region_song_level= (667,1786,827,1871)

level = ocr_region("SCR/1.png", region_song_level)
print(level)