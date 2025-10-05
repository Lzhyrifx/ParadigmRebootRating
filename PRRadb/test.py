import os
import subprocess
import imagehash
from PIL import Image
import pandas as pd
import logging
import numpy as np
import cv2

from rapidocr import RapidOCR, OCRVersion, EngineType, ModelType

logging.getLogger('RapidOCR').disabled = True

ocr = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)

# 1. ADB录屏
subprocess.run(["adb", "shell", "screenrecord", "--bit-rate", "4M", "--fps", "5", "/sdcard/score_record.mp4"])
subprocess.run(["adb", "pull", "/sdcard/score_record.mp4", "./score_record.mp4"])

# 2. 提取帧
os.makedirs("frames", exist_ok=True)
subprocess.run(["ffmpeg", "-i", "score_record.mp4", "-r", "5", "frames/frame_%04d.png"])

# 3. 固定区域去重
prev_hash = None
valid_frames = []
for frame_path in sorted(os.listdir("frames")):
    if not frame_path.endswith(".png"):
        continue
    img = Image.open(f"frames/{frame_path}")
    # 截取右侧分数显示区（需根据实际界面调整坐标）
    crop = img.crop((600, 100, 900, 700))
    current_hash = imagehash.phash(crop)
    # 若与前一帧哈希差异大，视为新歌曲
    if prev_hash is None or abs(current_hash - prev_hash) > 3:
        valid_frames.append(frame_path)
        prev_hash = current_hash

# 4. OCR提取数据
data = []
for frame_path in valid_frames:
    img = Image.open(f"frames/{frame_path}")

    # 转为 OpenCV 格式（RapidOCR 更推荐 numpy array）
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 分别截取歌名、曲师、分数区域（坐标需微调）
    song_name_roi = img_cv[150:250, 700:900]      # 歌名
    artist_roi = img_cv[260:300, 700:900]          # 曲师
    score_roi = img_cv[650:720, 600:750]           # 分数

    # OCR识别函数
    def get_text_from_ocr(roi_img):
        result = ocr(roi_img, use_cls=False, use_det=False, use_rec=True)
        if result and result.txts:
            return result.txts[0].strip()  # 取第一个识别结果
        return ""

    song_name = get_text_from_ocr(song_name_roi)
    artist = get_text_from_ocr(artist_roi)
    score = get_text_from_ocr(score_roi)

    data.append({"song": song_name, "artist": artist, "score": score})

# 5. 保存为Excel统计
df = pd.DataFrame(data)
df.to_excel("score_stat.xlsx", index=False)
print("统计完成！结果保存在score_stat.xlsx")