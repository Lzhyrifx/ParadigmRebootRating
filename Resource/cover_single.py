import httpx
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


def download_single_cover(song, save_folder="cover"):
    """单个封面下载任务"""
    title = song["title"]
    cover_url = song["cover_url"]

    # 生成保存文件名（处理特殊字符）
    filename = f"{title.lower().replace(' ', '').replace('-', '').replace('_', '').replace('(', '').replace(')', '').replace(':', '').replace('?', '').replace('×', '').replace('+', '').replace('&', '').replace('（', '').replace('）', '').replace('(', '').replace(')', '')}.png"
    save_path = os.path.join(save_folder, filename)

    # 跳过已存在的文件
    if os.path.exists(save_path):
        print(f"文件已存在，跳过：{title}")
        return (title, True, "文件已存在")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzhwiki/"
    }

    try:
        with httpx.Client() as client:
            response = client.get(cover_url, headers=headers, timeout=15)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"下载成功：{title}")
            return (title, True, "下载成功")

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP错误（{e.response.status_code}）"
        print(f"{error_msg}：{title}")
        return (title, False, error_msg)
    except httpx.TimeoutException:
        error_msg = "请求超时"
        print(f"{error_msg}：{title}")
        return (title, False, error_msg)
    except PermissionError:
        error_msg = "权限不足"
        print(f"{error_msg}：{title}")
        return (title, False, error_msg)
    except Exception as e:
        error_msg = f"未知错误：{str(e)}"
        print(f"{error_msg}：{title}")
        return (title, False, error_msg)


def download_covers_by_titles(song_titles, json_file="prr_songs_data.json", save_folder="cover", max_workers=5):
    """
    多线程下载指定歌曲的封面

    参数:
        song_titles: 歌曲标题列表
        json_file: JSON文件路径
        save_folder: 保存目录
        max_workers: 最大线程数
    """
    # 确保保存文件夹存在
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"已创建保存文件夹：{save_folder}")

    # 读取JSON数据
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            all_songs = json.load(f)
    except FileNotFoundError:
        print(f"错误：未找到JSON文件 {json_file}")
        return
    except json.JSONDecodeError:
        print(f"错误：JSON文件格式不正确")
        return

    # 筛选需要下载的歌曲
    target_songs = []
    for title in song_titles:
        found = False
        for song in all_songs:
            if song["title"].lower() == title.lower():
                target_songs.append(song)
                found = True
                break
        if not found:
            print(f"警告：未找到歌曲「{title}」")

    if not target_songs:
        print("没有需要下载的歌曲")
        return

    # 多线程下载
    print(f"开始下载，共{len(target_songs)}首歌曲，线程数：{max_workers}")
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(download_single_cover, song, save_folder): song for song in target_songs}

        # 获取结果
        for future in as_completed(futures):
            results.append(future.result())

    # 打印汇总信息
    print("\n下载完成，汇总信息：")
    success_count = sum(1 for res in results if res[1])
    fail_count = len(results) - success_count
    print(f"总任务：{len(results)}，成功：{success_count}，失败：{fail_count}")
    if fail_count > 0:
        print("失败列表：")
        for res in results:
            if not res[1]:
                print(f" - {res[0]}：{res[2]}")


# 使用示例
if __name__ == "__main__":
    # 要下载的歌曲列表
    songs_to_download = [
        "LABYRINTHOX", "ANOVA", "Argonovice",
        "名無しの宣教師", "炯眼の絶対零度", "soar to Ø"
    ]

    # 多线程下载（最多5个线程）
    download_covers_by_titles(
        song_titles=songs_to_download,
        max_workers=5  # 可根据网络情况调整线程数
    )