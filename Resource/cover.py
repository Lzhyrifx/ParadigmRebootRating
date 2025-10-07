import httpx
import os
import json


def download_cover_by_title(song_title, json_file="prr_songs_data.json", save_folder="cover"):
    """
    根据歌名从JSON文件中获取封面URL并下载图片

    参数:
        song_title: 要下载封面的歌曲名称
        json_file: 包含歌曲信息的JSON文件路径
        save_folder: 图片保存目录
    """
    # 确保保存文件夹存在
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"已创建保存文件夹：{save_folder}")

    # 读取JSON数据
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            songs = json.load(f)
    except FileNotFoundError:
        print(f"错误：未找到JSON文件 {json_file}")
        return
    except json.JSONDecodeError:
        print(f"错误：JSON文件格式不正确")
        return

    # 查找匹配的歌曲（不区分大小写）
    target_song = None
    for song in songs:
        if song["title"].lower() == song_title.lower():
            target_song = song
            break

    if not target_song:
        print(f"未找到歌曲：{song_title}")
        return

    # 提取封面URL和标题
    cover_url = target_song["cover_url"]
    actual_title = target_song["title"]
    print(f"找到歌曲「{actual_title}」，封面URL：{cover_url}")

    # 生成保存文件名（处理特殊字符）
    filename = f"{actual_title.lower().replace(' ', '').replace('-', '').replace('_', '').replace('(', '').replace(')', '').replace(':', '').replace('?', '').replace('×', '').replace('+', '').replace('&', '').replace('(', '').replace(')', '').replace('（', '').replace('）', '')}.png"
    save_path = os.path.join(save_folder, filename)

    # 跳过已存在的文件
    if os.path.exists(save_path):
        print(f"文件已存在，跳过：{save_path}")
        return

    # 下载图片
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzh.miraheze.org/"
    }

    try:
        with httpx.Client() as client:
            response = client.get(cover_url, headers=headers, timeout=15)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"下载成功：{save_path}")

    except httpx.HTTPStatusError as e:
        print(f"HTTP错误（{e.response.status_code}）：无法下载 {actual_title}")
    except httpx.TimeoutException:
        print(f"请求超时：{actual_title}")
    except PermissionError:
        print(f"权限不足：无法写入 {save_path}")
    except Exception as e:
        print(f"下载错误（{actual_title}）：{str(e)}")


# 使用示例
if __name__ == "__main__":
    # 测试下载几首歌曲的封面
    test_songs = ["ANOVA", "End time", "LABYRINTHOX", "名無しの宣教師"]
    for song in test_songs:
        download_cover_by_title(song)
        print("-" * 50)