import os
import json
import cv2
import re
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
from fuzzywuzzy import fuzz

# 初始化OCR引擎
engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)


def normalize_song_title(text):
    """标准化歌名，专注于关键字符匹配"""
    # 移除所有非字母数字字符，只保留核心内容
    normalized = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    return normalized


def enhanced_song_matching(ocr_song, candidate_songs, threshold=60):
    """增强版歌曲匹配算法"""
    best_match = None
    best_score = 0
    best_method = ""

    ocr_clean = normalize_song_title(ocr_song)
    print(f"🔍 标准化OCR歌名: '{ocr_song}' -> '{ocr_clean}'")

    for song in candidate_songs:
        song_title = song.get('title', '')
        song_clean = normalize_song_title(song_title)

        print(f"  对比: '{song_title}' -> '{song_clean}'")

        # 方法1: 部分匹配（主要方法）
        partial_score = fuzz.partial_ratio(ocr_clean, song_clean)

        # 方法2: 令牌排序匹配（考虑单词顺序）
        token_score = fuzz.token_sort_ratio(ocr_clean, song_clean)

        # 方法3: 简单包含检查
        contains_score = 100 if ocr_clean in song_clean or song_clean in ocr_clean else 0

        # 方法4: 关键字符匹配（特别针对 ma[xlzo 和 ma[χ]zo 这种情况）
        key_chars_match = 0
        if len(ocr_clean) >= 3:  # 至少有3个字符才进行关键字符匹配
            common_chars = set(ocr_clean) & set(song_clean)
            if len(common_chars) >= min(3, len(ocr_clean) - 1):  # 至少匹配大部分字符
                key_chars_match = 80 + min(20, len(common_chars) * 5)

        # 取最高分
        current_score = max(partial_score, token_score, contains_score, key_chars_match)
        current_method = ""
        if current_score == partial_score:
            current_method = "partial_ratio"
        elif current_score == token_score:
            current_method = "token_sort"
        elif current_score == contains_score:
            current_method = "contains"
        else:
            current_method = "key_chars"

        print(
            f"    分数: partial={partial_score}, token={token_score}, contains={contains_score}, key_chars={key_chars_match} -> 最终: {current_score}")

        if current_score > best_score and current_score >= threshold:
            best_score = current_score
            best_match = song
            best_method = current_method

    if best_match:
        print(f"🎯 最佳匹配: '{best_match.get('title', '')}' (分数: {best_score}, 方法: {best_method})")
    else:
        print(f"❌ 未找到达到阈值 {threshold} 的匹配")

    return best_match, best_score


def match_difficulty_artist_song(ocr_difficulty, ocr_artist, ocr_song, songs_data,
                                 difficulty_threshold=70, artist_threshold=70, song_threshold=60):  # 降低歌曲匹配阈值
    """按照难度→曲师→歌名的顺序进行匹配"""

    # 第一步：匹配难度
    print(f"\n第一步：匹配难度 '{ocr_difficulty}'")
    all_difficulties = list(set([song.get('difficulty', '') for song in songs_data]))
    matched_difficulty, diff_score = method_partial_ratio(ocr_difficulty, all_difficulties, difficulty_threshold)

    if not matched_difficulty:
        print(f"❌ 未找到匹配的难度")
        return None, None, None, 0

    print(f"✅ 匹配到难度: {matched_difficulty} (相似度: {diff_score}%)")

    # 第二步：在匹配的难度中匹配曲师
    print(f"\n第二步：在难度 '{matched_difficulty}' 中匹配曲师 '{ocr_artist}'")
    difficulty_artists = get_artists_by_difficulty(matched_difficulty, songs_data)

    # 查找所有相关的曲师变体
    all_artists = list(set([song.get('artist', '') for song in songs_data]))
    related_artists = find_related_artists(ocr_artist, all_artists)

    # 首先在难度相关的曲师中匹配
    available_artists = [artist for artist in difficulty_artists if artist in related_artists]

    if available_artists:
        print(f"🔍 找到 {len(available_artists)} 个相关曲师变体: {available_artists}")
        matched_artist, artist_score = method_partial_ratio(ocr_artist, available_artists, artist_threshold)
    else:
        # 如果没有找到难度相关的，在所有相关曲师中匹配
        print(f"⚠️  在难度 '{matched_difficulty}' 中未找到相关曲师，扩大搜索范围")
        matched_artist, artist_score = method_partial_ratio(ocr_artist, related_artists, artist_threshold)

    if not matched_artist:
        print(f"❌ 在难度 '{matched_difficulty}' 中未找到匹配的曲师")
        # 尝试在所有曲师中匹配
        all_artists = list(set([song.get('artist', '') for song in songs_data]))
        matched_artist, artist_score = method_partial_ratio(ocr_artist, all_artists, artist_threshold)
        if matched_artist:
            print(f"⚠️  在所有曲师中匹配到: {matched_artist} (相似度: {artist_score}%)")
        else:
            print(f"❌ 完全未找到匹配的曲师")
            return matched_difficulty, None, None, 0

    print(f"✅ 匹配到曲师: {matched_artist} (相似度: {artist_score}%)")

    # 第三步：在匹配的难度和曲师中匹配歌名
    print(f"\n第三步：在难度 '{matched_difficulty}' 和曲师 '{matched_artist}' 中匹配歌名 '{ocr_song}'")
    artist_songs = get_songs_by_artist_and_difficulty(matched_artist, matched_difficulty, songs_data)

    if artist_songs:
        print(f"曲师 '{matched_artist}' 在难度 '{matched_difficulty}' 下有 {len(artist_songs)} 首歌曲:")
        for i, song in enumerate(artist_songs, 1):
            print(f"  {i}. {song.get('title', 'N/A')} (等级: {song.get('level', 'N/A')})")

        # 使用增强版歌曲匹配
        matched_song, song_score = enhanced_song_matching(ocr_song, artist_songs, song_threshold)

        if matched_song:
            print(f"✅ 匹配到歌曲: {matched_song.get('title', 'N/A')} (相似度: {song_score}%)")
            total_score = (diff_score + artist_score + song_score) / 3
            return matched_difficulty, matched_artist, matched_song, total_score
        else:
            print(f"❌ 在该曲师的歌曲中未找到匹配的歌名")

            # 备选方案：尝试宽松匹配
            print(f"\n🔄 尝试宽松匹配...")
            matched_song, song_score = enhanced_song_matching(ocr_song, artist_songs, threshold=40)  # 降低阈值
            if matched_song:
                print(f"🎉 宽松匹配成功: {matched_song.get('title', 'N/A')} (相似度: {song_score}%)")
                total_score = (diff_score + artist_score + song_score) / 3
                return matched_difficulty, matched_artist, matched_song, total_score
    else:
        print(f"❌ 曲师 '{matched_artist}' 在难度 '{matched_difficulty}' 下没有歌曲")

    # 如果在前三步没找到，尝试在曲师的所有歌曲中匹配
    print(f"\n备选方案：在曲师 '{matched_artist}' 的所有歌曲中匹配")
    all_artist_songs = [song for song in songs_data if song.get('artist', '').lower() == matched_artist.lower()]
    if all_artist_songs:
        print(f"曲师 '{matched_artist}' 共有 {len(all_artist_songs)} 首歌曲:")
        for i, song in enumerate(all_artist_songs, 1):
            print(
                f"  {i}. {song.get('title', 'N/A')} - {song.get('difficulty', 'N/A')} (等级: {song.get('level', 'N/A')})")

        matched_song, song_score = enhanced_song_matching(ocr_song, all_artist_songs, song_threshold)
        if matched_song:
            print(
                f"✅ 匹配到歌曲: {matched_song.get('title', 'N/A')} (难度: {matched_song.get('difficulty', 'N/A')}) (相似度: {song_score}%)")
            total_score = (diff_score + artist_score + song_score) / 3
            return matched_difficulty, matched_artist, matched_song, total_score

    print(f"❌ 最终未找到匹配的歌曲")
    return matched_difficulty, matched_artist, None, 0


# 其他函数保持不变（load_songs_data, ocr_region, distinguish, get_level, clean_ocr_text,
# extract_base_artist_name, find_related_artists, method_partial_ratio,
# get_artists_by_difficulty, get_songs_by_artist_and_difficulty, process_screenshot,
# save_results_to_json, main）

# 区域坐标定义
region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_artist1 = (1000, 351, 2200, 425)

region_song2 = (1603, 454, 3016, 535)
region_artist2 = (1681, 555, 3018, 624)
region_rating2 = (1946, 1485, 2420, 1596)