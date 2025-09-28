import json
import os
import re
from rapidfuzz import fuzz, process
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import cv2


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
    if result == "type1":
        x, y = 1590, 441
        b, g, r = img[y, x]
        if 210 <= r <= 225 and 135 <= g <= 150 and 235 <= b <= 255:
            return "Massive"
        elif 225 <= r <= 238 and 108 <= g <= 120 and 105 <= b <= 120:
            return "Invaded"
        else:
            return "Detected"
    if result == "type2":
        x, y = 2982, 1520
        b, g, r = img[y, x]
        if 170 <= r <= 190 and 120 <= g <= 135 and 200 <= b <= 215:
            return "Massive"
        elif 195 <= r <= 210 and 110 <= g <= 120 and 105 <= b <= 120:
            return "Invaded"
        else:
            return "Detected"

def ocr_optimize(text):
    return text.replace('/', '').replace('、', '').replace(',', '').replace('.', '')

def scr_type(region_song,region_artist,region_rating):
    song_name = os.path.splitext(filename)[0]

    result_song_obj = ocr_region(img_path, region_song)
    result_artist_obj = ocr_region(img_path, region_artist)
    result_rating_obj = ocr_region(img_path, region_rating)

    result_song_obj.vis("Result/" + song_name + ".jpg")
    result_artist_obj.vis("Result/" + song_name + "ART.jpg")
    result_rating_obj.vis("Result/" + song_name + "RAT.jpg")

    result_level = level(img_path)

    result_song = ocr_optimize(result_song_obj.txts[0] if result_song_obj.txts else "")
    result_artist = ocr_optimize(result_artist_obj.txts[0] if result_artist_obj.txts else "")
    result_rating= ocr_optimize(result_rating_obj.txts[0] if result_rating_obj.txts else "")
    print(result_level)
    print(result_song)
    print(result_artist)
    print(result_rating)

    return result_song, result_artist, result_rating, result_level


def method_hierarchical_match(items, song, artist, difficulty):
    if not items:
        return None, 0

    filtered_items = [item for item in items if item['difficulty'] == difficulty]

    if not filtered_items:
        return None, 0

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
        return best_match, match_score

    print("所有级别匹配均失败")
    return None, 0

# 加载JSON数据
def load_json_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


json_file_path = "songs_data.json"  # 你的JSON文件路径

# 加载所有歌曲数据
all_songs_data = load_json_data(json_file_path)



difficulty_points = {"Massive": (2687, 1780),"Invaded": (2416, 1780),"Detected": (2132, 1780),}

region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_artist1 = (1000,351,2200,425)

region_song2 = (1603,454,3016,535)
region_artist2 = (1681,555,3018,624)
region_rating2 = (1946, 1485, 2420, 1596)
src_folder = "SCR"

for filename in os.listdir(src_folder):
    if filename.upper().endswith('.JPG'):
        img_path = os.path.join(src_folder, filename)
        result = distinguish(img_path)

        if result == "type1":
            final_result = scr_type(region_song1, region_artist1, region_rating1)
        elif result == "type2":
            final_result = scr_type(region_song2, region_artist2, region_rating2)
        else:
            continue

        result_song, result_artist, result_rating, result_difficulty = final_result

        match_result, score = method_hierarchical_match(
            items=all_songs_data,
            song=result_song,
            artist=result_artist,
            difficulty=result_difficulty
        )

