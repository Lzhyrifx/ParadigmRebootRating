import requests
import json


def get_all_songs_levels():
    url = "https://api.prp.icel.site/songs/"
    response = requests.get(url)
    response.raise_for_status()
    songs_data = response.json()
    return songs_data


if __name__ == "__main__":
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

    print(f"\n已保存 {len(simplified_songs)} 首歌曲信息到 songs_data.json")