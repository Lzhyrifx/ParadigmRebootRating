import json
import os
import time
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

from rapidfuzz import fuzz, process
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import cv2
import logging

logging.getLogger('RapidOCR').disabled = True

# 全局变量
bounds = [900000, 930000, 950000, 970000, 980000, 990000]
rewards = [3, 1, 1, 1, 1, 1]
EPS = 0.00002

# 区域定义
difficulty_points = {"Massive": (2687, 1780), "Invaded": (2416, 1780), "Detected": (2132, 1780)}
region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_song_mini1 = (1435, 266, 1754, 340)
region_artist1 = (1000, 351, 2200, 425)
region_rating2 = (1946, 1485, 2420, 1596)
region_song2 = (1603, 454, 3016, 535)
region_song_mini2 = (2598, 454, 3016, 545)
region_artist2 = (1681, 555, 3018, 624)


class AsyncOCRProcessor:
    def __init__(self, max_workers=None):
        self.engine = RapidOCR(
            params={
                "Rec.ocr_version": OCRVersion.PPOCRV5,
                "Rec.engine_type": EngineType.ONNXRUNTIME,
                "Rec.model_type": ModelType.MOBILE,
            }
        )
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.get_event_loop()

    async def ocr_region(self, image_path, region_coords):
        def _sync_ocr():
            img = cv2.imread(image_path)
            x1, y1, x2, y2 = region_coords
            roi = img[y1:y2, x1:x2]
            res = self.engine(roi, use_cls=False, use_det=False, use_rec=True)
            return res

        return await self.loop.run_in_executor(self.thread_pool, _sync_ocr)

    async def distinguish(self, image_path):
        def _sync_distinguish():
            img = cv2.imread(image_path)
            x, y = 27, 1934
            b, g, r = img[y, x]
            return "type2" if (60 <= r <= 66 and 136 <= g <= 142 and 170 <= b <= 176) else "type1"

        return await self.loop.run_in_executor(self.thread_pool, _sync_distinguish)

    async def level(self, image_path, result_type):
        def _sync_level():
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

        return await self.loop.run_in_executor(self.thread_pool, _sync_level)


def ocr_optimize(text):
    return text.replace('/', '').replace('、', '').replace(',', '').replace('.', '')


async def scr_ocr(ocr_processor, img_path, filename, region_song, region_artist, region_rating, region_song_mini,
                  result_type):
    mini_region = False
    song_name = os.path.splitext(filename)[0]

    result_song_obj = await ocr_processor.ocr_region(img_path, region_song)
    if not result_song_obj or not result_song_obj.txts or not result_song_obj.txts[0].strip():
        backup_region = region_song_mini
        mini_region = True
        result_song_obj = await ocr_processor.ocr_region(img_path, backup_region)

    result_artist_obj = await ocr_processor.ocr_region(img_path, region_artist)
    result_rating_obj = await ocr_processor.ocr_region(img_path, region_rating)

    # 保存结果图片（可选，如果需要可以取消注释）
    # result_song_obj.vis("Result/" + song_name + ".jpg")
    # result_artist_obj.vis("Result/" + song_name + "ART.jpg")
    # result_rating_obj.vis("Result/" + song_name + "RAT.jpg")

    result_song_ocr = ocr_optimize(result_song_obj.txts[0] if result_song_obj.txts else "")
    result_artist_ocr = ocr_optimize(result_artist_obj.txts[0] if result_artist_obj.txts else "")
    result_rating_ocr = ocr_optimize(result_rating_obj.txts[0] if result_rating_obj.txts else "")
    result_rating_ocr = result_rating_ocr.lstrip('0')

    print(f"处理 {filename}:")
    print(f"  歌曲: {result_song_ocr}")
    print(f"  艺术家: {result_artist_ocr}")
    print(f"  分数: {result_rating_ocr}")

    return result_song_ocr, result_artist_ocr, result_rating_ocr, mini_region


def single_rating(level: float, score: int) -> float:
    global bounds, rewards
    rating: float = 0

    score = min(score, 1010000)

    if score >= 1009000:
        rating = level * 10 + 7 + 3 * (((score - 1009000) / 1000) ** 1.35)
    elif score >= 1000000:
        rating = 10 * (level + 2 * (score - 1000000) / 30000)
    else:
        for bound, reward in zip(bounds, rewards):
            rating += reward if score >= bound else 0
        rating += 10 * (level * ((score / 1000000) ** 1.5) - 0.9)

    rating = max(.0, rating)
    int_rating: int = int(rating * 100 + EPS)
    return int_rating


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
        return best_match, match_score

    return None, 0


async def load_json_data(json_path):
    async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content)


async def save_to_json(match_result, score, result_score, filename, output_file="songs_results.json"):
    try:
        score_int = int(result_score)
        song_level = match_result.get('level', 0)
        rating = single_rating(song_level, score_int)
    except (ValueError, TypeError) as e:
        rating = 0

    result_data = {
        "title": match_result['title'],
        "artist": match_result['artist'],
        "difficulty": match_result['difficulty'],
        "song_level_id": match_result.get('song_level_id', ''),
        "b15": match_result.get('b15', False),
        "level": match_result.get('level', ''),
        "score": result_score,
        "rating": rating / 100
    }

    # 读取现有数据
    existing_data = []
    if os.path.exists(output_file):
        try:
            async with aiofiles.open(output_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                if content.strip():
                    data = json.loads(content)
                    if isinstance(data, dict) and "b35" in data and "b15" in data:
                        existing_data = data["b35"] + data["b15"]
                    elif isinstance(data, list):
                        existing_data = data
                    else:
                        existing_data = []
        except (json.JSONDecodeError, Exception) as e:
            existing_data = []
    else:
        existing_data = []

    # 更新或添加数据
    found_existing = False
    for i, item in enumerate(existing_data):
        if isinstance(item, dict) and item.get('song_level_id') == result_data['song_level_id']:
            found_existing = True
            existing_score = int(item.get('score', 0))
            new_score = int(result_score)

            if new_score > existing_score:
                existing_data[i] = result_data
                print(f"更新记录: {result_data['title']} 分数 {existing_score} -> {new_score}")
            else:
                print(f"跳过保存: {result_data['title']} 当前分数 {existing_score} 小于或等于新分数 {new_score}")
            break

    if not found_existing:
        existing_data.append(result_data)
        print(f"添加新记录: {result_data['title']} 分数 {result_score}")

    # 保存数据
    async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(existing_data, ensure_ascii=False, indent=2))


def best(input_file="songs_results.json"):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and "b35" in data and "b15" in data:
            b35 = data["b35"]
            b15 = data["b15"]
        elif isinstance(data, list):
            b35 = [item for item in data if not item.get('b15', False)]
            b15 = [item for item in data if item.get('b15', False)]
        else:
            return None

        b35_sorted = sorted(b35, key=lambda x: x['rating'], reverse=True)
        b15_sorted = sorted(b15, key=lambda x: x['rating'], reverse=True)

        sorted_data = {
            "b35": b35_sorted,
            "b15": b15_sorted
        }

        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=2)

        return sorted_data
    except Exception as e:
        print(f"排序错误: {e}")
        return None


async def process_single_image(ocr_processor, all_songs_data, filename, src_folder):
    """处理单个图片的异步函数"""
    img_path = os.path.join(src_folder, filename)

    try:
        # 并行执行类型检测和级别检测
        result_type, result_level = await asyncio.gather(
            ocr_processor.distinguish(img_path),
            ocr_processor.level(img_path, await ocr_processor.distinguish(img_path))
        )

        if result_level == "ERROR":
            print(f"跳过 {filename}: 无法识别级别")
            return

        # 选择区域
        if result_type == "type1":
            final_result = await scr_ocr(
                ocr_processor, img_path, filename,
                region_song1, region_artist1, region_rating1, region_song_mini1, result_type
            )
        elif result_type == "type2":
            final_result = await scr_ocr(
                ocr_processor, img_path, filename,
                region_song2, region_artist2, region_rating2, region_song_mini2, result_type
            )
        else:
            return

        result_song, result_artist, result_rating, mini_region = final_result

        # 匹配歌曲
        match_result, score = method_hierarchical_match(
            items=all_songs_data,
            song=result_song,
            artist=result_artist,
            difficulty=result_level,
            mini_match=mini_region
        )

        if match_result:
            await save_to_json(match_result, score, result_rating, filename)
        else:
            print(f"ERROR: 无法匹配 {filename}")

        print("\n")

    except Exception as e:
        print(f"处理 {filename} 时出错: {e}")


async def main():
    start_time = time.time()

    # 初始化OCR处理器
    ocr_processor = AsyncOCRProcessor(max_workers=8)  # 可以调整线程数

    # 加载歌曲数据
    json_file_path = "songs_data.json"
    all_songs_data = await load_json_data(json_file_path)

    src_folder = "SCR"

    # 获取所有图片文件
    image_files = [f for f in os.listdir(src_folder) if f.upper().endswith('.JPG')]

    print(f"找到 {len(image_files)} 个图片文件，开始并行处理...")

    # 创建任务列表
    tasks = [
        process_single_image(ocr_processor, all_songs_data, filename, src_folder)
        for filename in image_files
    ]

    # 限制并发数，避免资源竞争
    semaphore = asyncio.Semaphore(5)  # 同时处理3个图片

    async def bounded_task(task):
        async with semaphore:
            return await task

    # 执行所有任务
    await asyncio.gather(*[bounded_task(task) for task in tasks])

    # 排序结果
    best()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")
    print(f"平均每个图片: {elapsed_time / len(image_files):.2f} 秒")


if __name__ == "__main__":
    asyncio.run(main())