import time
import httpx
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


def download_single(song, save_folder, headers, max_retries=2, retry_delay=1.0):
    title = song["title"]
    artist = song["artist"]
    cover_url = song["cover_url"]

    # 处理文件名特殊字符（保持不变）
    processed_title = (
        title.lower()
        .replace(' ', '_')
        .replace('\\', '')
        .replace('-', '')
        .replace('/', '')
        .replace(':', '')
        .replace("'", '')
        .replace('?', '')
        .replace('|', '')
        .replace('!', '')
        .replace('*', '')
        .replace('.', '')
        .replace(',', '')
        .replace('[', '')
        .replace(']', '')
        .replace(';', '')
        .replace('↑', '')
        .replace('↓', '')
        .replace('&', '')
        .replace('<', '')
        .replace('>', '')
        .replace('—', '')
        .replace('(', '')
        .replace(')', '')
        .replace('✧', '')
        .replace('･', '')
        .replace('ﾟ', '')
        .replace('•', '')
        .replace('+', '')
        .replace('｡', '')
        .replace('：', '')
        .replace('~', '')
        .replace('†', '')
        .replace('#', '')
        .replace('@', '')
        .replace('$', '')
        .replace('%', '')
        .replace('^', '')
        .replace('"', '')
        .replace('=', '')
        .replace('¿', '')
        .replace('『', '')
        .replace('』', '')
        .replace('・', '')
    )

    processed_artist = (
        artist.lower()
        .replace(' ', '_')
        .replace('\\', '')
        .replace('-', '')
        .replace('/', '')
        .replace(':', '')
        .replace("'", '')
        .replace('?', '')
        .replace('|', '')
        .replace('!', '')
        .replace('*', '')
        .replace('.', '')
        .replace(',', '')
        .replace('[', '')
        .replace(']', '')
        .replace(';', '')
        .replace('↑', '')
        .replace('↓', '')
        .replace('&', '')
        .replace('<', '')
        .replace('>', '')
        .replace('—', '')
        .replace('(', '')
        .replace(')', '')
        .replace('✧', '')
        .replace('･', '')
        .replace('ﾟ', '')
        .replace('•', '')
        .replace('+', '')
        .replace('｡', '')
        .replace('：', '')
        .replace('~', '')
        .replace('†', '')
        .replace('#', '')
        .replace('@', '')
        .replace('$', '')
        .replace('%', '')
        .replace('^', '')
        .replace('"', '')
        .replace('=', '')
        .replace('¿', '')
        .replace('『', '')
        .replace('』', '')
        .replace('・', '')
    )

    filename = f"{processed_title}_{processed_artist}.png"
    save_path = os.path.join(save_folder, filename)
    relative_path = os.path.join(save_folder, filename)

    if os.path.exists(save_path):
        song["cover_path"] = relative_path
        return (title, True, "文件已存在", song)

    for attempt in range(max_retries):
        try:
            with httpx.Client() as client:
                response = client.get(cover_url, headers=headers, timeout=15)
                response.raise_for_status()

                with open(save_path, "wb") as f:
                    f.write(response.content)

                song["cover_path"] = relative_path
                return (title, True, f"下载成功（第{attempt + 1}次尝试）", song)

        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                if isinstance(e, httpx.HTTPStatusError):
                    return (title, False, f"HTTP错误（{e.response.status_code}）", song)
                elif isinstance(e, httpx.TimeoutException):
                    return (title, False, "请求超时", song)
                else:
                    return (title, False, f"网络错误：{str(e)}", song)
        except PermissionError:
            return (title, False, "权限不足（可能文件被占用）", song)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return (title, False, f"未知错误：{str(e)}", song)

    return (title, False, "重试耗尽", song)


def download_all_covers(json_file, save_folder="Cover", max_workers=8):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"已创建保存文件夹：{save_folder}")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 保留原始结构（包含b35和b15）
            # 提取两个分组的歌曲列表（不合并结构）
            b35_songs = data.get("b35", [])
            b15_songs = data.get("b15", [])
            all_songs = b35_songs + b15_songs  # 仅用于批量提交下载任务
    except FileNotFoundError:
        print(f"错误：未找到JSON文件 {json_file}")
        return
    except json.JSONDecodeError:
        print(f"错误：JSON文件格式不正确")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzh.miraheze.org/"
    }

    print(f"开始下载所有封面，共{len(all_songs)}首歌曲（b35: {len(b35_songs)}, b15: {len(b15_songs)}），线程数：{max_workers}")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(download_single, song, save_folder, headers)
            for song in all_songs
        ]

        for future in as_completed(futures):
            results.append(future.result())

    # 关键修改：保持原始结构，只更新内部歌曲的cover_path
    # （因为列表中的歌曲对象是引用类型，处理后原始b35_songs和b15_songs已经被修改）
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            # 写回原始结构（包含b35和b15）
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n已将封面路径信息更新到 {json_file}（保留b35和b15结构）")
    except Exception as e:
        print(f"\n更新JSON文件失败：{str(e)}")

    print("\n下载完成，汇总信息：")
    success_count = sum(1 for res in results if res[1])
    fail_count = len(results) - success_count
    print(f"总任务：{len(results)}，成功：{success_count}，失败：{fail_count}")

    if fail_count > 0:
        print("\n失败列表：")
        for title, status, msg, _ in results:
            if not status:
                print(f" - {title}：{msg}")


if __name__ == "__main__":
    download_all_covers("songs_results.json")  # 注意这里用原始文件名，避免覆盖问题