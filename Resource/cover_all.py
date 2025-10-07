import httpx
import os
import json

def download_cover_from_json(json_file, save_folder="cover"):
    # 确保保存文件夹存在
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"已创建保存文件夹：{save_folder}")

    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as f:
        songs = json.load(f)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzh.miraheze.org/"
    }

    with httpx.Client() as client:
        for song in songs:
            title = song["title"]
            cover_url = song["cover_url"]
            print(f"处理歌曲：{title}，URL：{cover_url}")

            filename = f"{title.lower().replace(' ', '').replace('-', '').replace('_', '').replace('(', '').replace(')', '').replace(':', '').replace('?', '')}.png"
            save_path = os.path.join(save_folder, filename)

            if os.path.exists(save_path):
                print(f"文件已存在，跳过：{save_path}\n")
                continue

            try:
                response = client.get(cover_url, headers=headers, timeout=15)
                response.raise_for_status()

                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"下载成功：{save_path}\n")

            except httpx.HTTPStatusError as e:
                print(f"HTTP错误（{e.response.status_code}）：{title}\n")
            except httpx.TimeoutException:
                print(f"请求超时：{title}\n")
            except PermissionError:
                print(f"权限不足：无法写入 {save_path}\n")
            except Exception as e:
                print(f"未知错误（{title}）：{str(e)}\n")


if __name__ == "__main__":
    download_cover_from_json("prr_songs_data.json")