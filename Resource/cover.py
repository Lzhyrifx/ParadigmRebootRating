import httpx
import os
from bs4 import BeautifulSoup

def download_cover_by_songname(song_name, save_folder="cover"):
    song_keyword = song_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    file_detail_url = f"https://paradigmrebootzh.miraheze.org/wiki/文件:Cover_{song_keyword}.png"
    print(f"生成曲名「{song_name}」的文件详情页URL：{file_detail_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzh.miraheze.org/"
    }

    with httpx.Client() as client:
        try:
            response = client.get(file_detail_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            full_media_div = soup.find("div", class_="fullMedia")
            if not full_media_div:
                print(f"未找到原始图片区域")
                return
            original_img_link = full_media_div.find("a")
            if not original_img_link or "href" not in original_img_link.attrs:
                print(f"未提取到真实图片URL")
                return
            real_img_url = original_img_link["href"]

            if real_img_url.startswith("//"):
                real_img_url = "https:" + real_img_url
            print(f"提取到真实图片URL：{real_img_url}")

            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
                print(f"已创建保存文件夹：{save_folder}")

            img_filename = f"{song_keyword}.png"
            save_path = os.path.join(save_folder, img_filename)

            if os.path.exists(save_path):
                print(f"文件已存在，跳过下载：{save_path}")
                return

            img_response = client.get(real_img_url, headers=headers, timeout=15)
            img_response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(img_response.content)
            print(f"保存路径：{save_path}\n")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"404：曲名「{song_name}」对应的页面不存在\n")
            else:
                print(f"HTTP错误（{e.response.status_code}）：{str(e)}\n")
        except httpx.TimeoutException:
            print(f"请求超时：曲名「{song_name}」\n")
        except PermissionError:
            print(f"权限不足：无法写入「{save_folder}」文件夹\n")
        except Exception as e:
            print(f"未知错误（{song_name}）：{str(e)}\n")


if __name__ == "__main__":
    target_songs = ["Abyssgazer", "Anova", "Argonovice"]
    for song in target_songs:
        download_cover_by_songname(song_name=song)
