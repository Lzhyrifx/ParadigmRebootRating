import json
import os
from pathlib import Path

def load_songs_data(filename):
    root_dir = Path(__file__).parent
    json_path = root_dir / filename  # 拼接路径
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filename, indent=2):
    root_dir = Path(__file__).parent
    json_path = root_dir / filename
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    print(f"数据已成功保存到 {filename}")


def load_prr_songs_data():
    return load_songs_data("prr_songs_data.json")
