import json
import os
from rapidfuzz import fuzz, process
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import cv2
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

def distinguish(image_path):
    img = cv2.imread(image_path)
    x, y = 27, 1934
    b, g, r = img[y, x]
    return "type2" if (60 <= r <= 66 and 136 <= g <= 142 and 170 <= b <= 176) else "type1"

def level(image_path):
    img = cv2.imread(image_path)
    if result_type == "type1":
        x, y = 1590, 441
        b, g, r = img[y, x]
        if 210 <= r <= 225 and 135 <= g <= 150 and 235 <= b <= 255:
            return "Massive"
        elif 225 <= r <= 238 and 108 <= g <= 120 and 105 <= b <= 120:
            return "Invaded"
        elif 100 <= r <= 115 and 190 <= g <= 205 and 240 <= b <= 255:
            return "Detected"
        else:
            return "ERROR"
    if result_type == "type2":
        x, y = 2982, 1520
        b, g, r = img[y, x]
        if 170 <= r <= 190 and 120 <= g <= 135 and 200 <= b <= 215:
            return "Massive"
        elif 195 <= r <= 210 and 110 <= g <= 120 and 105 <= b <= 120:
            return "Invaded"
        elif 120 <= r <= 135 and 170 <= g <= 185 and 205 <= b <= 220:
            return "Detected"
        else:
            return "ERROR"

def ocr_optimize(text):
    return text.replace('/', '').replace('、', '').replace(',', '').replace('.', '')

def scr_ocr(region_song,region_artist,region_rating):
    mini_region = False
    song_name = os.path.splitext(filename)[0]

    result_song_obj = ocr_region(img_path, region_song)
    if not result_song_obj or not result_song_obj.txts or not result_song_obj.txts[0].strip():

        if result_type == "type1":
            backup_region = region_song_mini1
        else:
            backup_region = region_song_mini2
        mini_region = True

        result_song_obj = ocr_region(img_path, backup_region)
    result_artist_obj = ocr_region(img_path, region_artist)
    result_rating_obj = ocr_region(img_path, region_rating)

    result_song_obj.vis("Result/" + song_name + ".jpg")
    result_artist_obj.vis("Result/" + song_name + "ART.jpg")
    result_rating_obj.vis("Result/" + song_name + "RAT.jpg")


    result_song_ocr = ocr_optimize(result_song_obj.txts[0] if result_song_obj.txts else "")
    result_artist_ocr = ocr_optimize(result_artist_obj.txts[0] if result_artist_obj.txts else "")
    result_rating_ocr= ocr_optimize(result_rating_obj.txts[0] if result_rating_obj.txts else "")

    print(result_song_ocr)
    print(result_artist_ocr)
    print(result_rating_ocr)

    return result_song_ocr, result_artist_ocr, result_rating_ocr,mini_region


def method_hierarchical_match(items, song, artist, difficulty, mini_match=False):
    if not items:
        return None, 0

    filtered_items = [item for item in items if item['difficulty'] == difficulty]

    if not filtered_items:
        return None, 0

    if mini_match and len(song.strip()) <= 7:
        short_title_items = [item for item in filtered_items if len(item['title']) <= 7]
        if short_title_items:
            filtered_items = short_title_items
    compare_texts = [f"{item['title']} {item['artist']}" for item in filtered_items]

    query_text = f"{song} {artist}"

    result_match = process.extractOne(
        query_text,
        compare_texts,
        scorer=fuzz.partial_ratio,
        score_cutoff=50
    )

    if result_match:
        matched_text, match_score, index = result_match
        best_match = filtered_items[index]
        print(f"匹配成功: {best_match['title']} - {best_match['artist']} (置信度: {match_score:.1f})")
        print("\n")
        return best_match, match_score

    return None, 0

def load_json_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


json_file_path = "songs_data.json"  # 你的JSON文件路径

all_songs_data = load_json_data(json_file_path)

difficulty_points = {"Massive": (2687, 1780),"Invaded": (2416, 1780),"Detected": (2132, 1780),}

region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_song_mini1 = (1435,266,1754,340)
region_artist1 = (1000,351,2200,425)

region_rating2 = (1946, 1485, 2420, 1596)
region_song2 = (1603,454,3016,535)
region_song_mini2 = (2598,454,3016,545)
region_artist2 = (1681,555,3018,624)

src_folder = "SCR"

for filename in os.listdir(src_folder):
    if filename.upper().endswith('.JPG'):
        img_path = os.path.join(src_folder, filename)
        result_type = distinguish(img_path)

        result_level = level(img_path)
        if result_level == "ERROR":
            print(f" {filename}: 无法识别难度")
            continue
        if result_type == "type1":
            final_result = scr_ocr(region_song1, region_artist1, region_rating1)
        elif result_type == "type2":
            final_result = scr_ocr(region_song2, region_artist2, region_rating2)
        else:
            continue

        result_song, result_artist, result_rating ,mini_region= final_result

        match_result, score = method_hierarchical_match(
            items=all_songs_data,
            song=result_song,
            artist=result_artist,
            difficulty=result_level,
            mini_match= mini_region
        )

