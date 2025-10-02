def optimized_main():
    start_time = time.time()

    # 获取所有图片文件
    image_files = [f for f in os.listdir(src_folder) if f.upper().endswith('.JPG')]
    results_batch = []

    # 使用线程池并行处理（适合I/O密集型）
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {
            executor.submit(process_single_image_optimized, f): f
            for f in image_files
        }

        for future in concurrent.futures.as_completed(future_to_file):
            result = future.result()
            if result:
                results_batch.append(result)

    # 批量保存结果
    if results_batch:
        batch_save_to_json(results_batch)

    best()
    end_time = time.time()
    print(f"优化后执行耗时: {end_time - start_time:.2f} 秒")


def process_single_image_optimized(filename):
    """优化后的单图片处理函数"""
    img_path = os.path.join(src_folder, filename)

    # 快速类型判断
    result_type = distinguish(img_path)
    result_level = level(img_path)

    if result_level == "ERROR":
        return None

    # OCR区域识别
    if result_type == "type1":
        final_result = scr_ocr(region_song1, region_artist1, region_rating1)
    else:
        final_result = scr_ocr(region_song2, region_artist2, region_rating2)

    result_song, result_artist, result_rating, mini_region = final_result

    # 使用缓存的歌曲数据
    songs_data = get_songs_data()
    match_result, score = method_hierarchical_match(
        items=songs_data,
        song=result_song,
        artist=result_artist,
        difficulty=result_level,
        mini_match=mini_region
    )

    if match_result:
        return match_result, result_rating, filename
    return None