import json

# 读取原始JSON数据
with open('songs_data_test.json', 'r', encoding='utf-8') as f:
    original_data = json.load(f)

# 用于存储处理后的数据
result = []
# 用于跟踪已处理的歌曲（通过标题和艺术家区分）
processed_songs = set()

for item in original_data:
    # 创建唯一标识一首歌曲的键
    song_key = (item['title'], item['artist'])

    if song_key not in processed_songs:
        # 新歌曲，初始化数据结构
        new_song = {
            "title": item['title'],
            "artist": item['artist'],
            "b15": item['b15'],
            "cover_url": "",  # 封面URL需要后续补充
            "charts": {}
        }

        # 查找该歌曲的所有难度数据
        for chart in original_data:
            if (chart['title'], chart['artist']) == song_key:
                difficulty = chart['difficulty'].lower()  # 转为小写
                new_song['charts'][difficulty] = {
                    "level": chart['level'],
                    "song_level_id": chart['song_level_id']
                }

        result.append(new_song)
        processed_songs.add(song_key)

# 输出处理后的JSON（缩进2空格，确保中文正常显示）
with open('prr_songs_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"转换完成，共处理 {len(result)} 首歌曲")