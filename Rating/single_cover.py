import os
import time

import httpx


def download_single(song, save_folder, headers, max_retries=2, retry_delay=1.0):
    title = song["title"]
    artist = song["artist"]
    cover_url = song["cover_url"]

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
        .replace('・', '')
    )


    filename = f"{processed_title}_{processed_artist}.png"
    save_path = os.path.join(save_folder, filename)
    relative_path = filename

    if os.path.exists(save_path):
        song["cover"] = relative_path
        return title, True, "文件已存在", song

    for attempt in range(max_retries):
        try:
            with httpx.Client() as client:
                response = client.get(cover_url, headers=headers, timeout=15)
                response.raise_for_status()

                with open(save_path, "wb") as f:
                    f.write(response.content)

                song["cover"] = relative_path
                return title, True, f"下载成功（第{attempt + 1}次尝试）", song

        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                if isinstance(e, httpx.HTTPStatusError):
                    return title, False, f"HTTP错误（{e.response.status_code}）", song
                elif isinstance(e, httpx.TimeoutException):
                    return title, False, "请求超时", song
                else:
                    return title, False, f"网络错误：{str(e)}", song
        except PermissionError:
            return title, False, "权限不足（可能文件被占用）", song
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return title, False, f"未知错误：{str(e)}", song

    return title, False, "重试耗尽", song