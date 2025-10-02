import httpx
import json
import time


def get_all_songs_levels():
    start_time = time.time()

    url = "https://api.prp.icel.site/songs"
    response = httpx.get(url)
    response.raise_for_status()
    songs_data = response.json()

    end_time = time.time()
    print(f"API耗时: {end_time - start_time:.2f} 秒")

    return songs_data


if __name__ == "__main__":
    start_time = time.time()

    songs = get_all_songs_levels()

    simplified_songs = []
    for song in songs:
        simplified_song = {
            "title": song.get("title", "N/A"),
            "artist": song.get("artist", "N/A"),
            "difficulty": song.get("difficulty", "N/A"),
            "level": song.get("level", "N/A"),
            "song_level_id": song.get("song_level_id", "N/A"),
            "b15": song.get("b15", "N/A"),
        }
        simplified_songs.append(simplified_song)

    with open('songs_data.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_songs, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"\n已保存 {len(simplified_songs)} 首歌曲信息到 songs_data.json")
    print(f"程序总执行耗时: {elapsed_time:.2f} 秒")