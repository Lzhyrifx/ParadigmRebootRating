import json

# 读取JSON数据
with open('prr_songs_data.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

# 调整每个歌曲的charts顺序
for song in songs:
    if 'charts' in song:
        # 按照指定顺序重新构建charts字典
        song['charts'] = {
            'detected': song['charts']['detected'],
            'invaded': song['charts']['invaded'],
            'massive': song['charts']['massive']
        }

# 保存修改后的数据
with open('prr_songs_data.json', 'w', encoding='utf-8') as f:
    json.dump(songs, f, ensure_ascii=False, indent=2)

print("已完成charts顺序调整，结果保存至prr_songs_data_updated.json")