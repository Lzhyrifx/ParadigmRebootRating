import cv2
from rapidfuzz import fuzz, process
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import logging
from function import ocr_region,init_device


region_song_level= (624,1668,894,1911)

level = ocr_region("Temp/test.png", *region_song_level)
print(level)