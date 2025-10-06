import httpx
import os
import json
import signal
import urllib.parse
from bs4 import BeautifulSoup

cover_urls = []
processed_titles = set()
SPECIAL_TITLE_MAP = {
    "Cipher : /2&//<|0": "Cipher"
}

def signal_handler(signal, frame):
    print("\n正在保存已处理结果...")
    save_results()
    print(f"已保存 {len(cover_urls)} 条记录到 cover_url.json")
    exit(0)

def normalize_title_for_wiki(title: str) -> str:
    title = (title.
             replace('[', '［').
             replace(']', '］').
             replace('/', '／').
             replace('#', '＃'))
    return title
def save_results():
    with open("cover_url.json", "w", encoding="utf-8") as f:
        json.dump(cover_urls, f, ensure_ascii=False, indent=2)


def get_cover_url(song_name):
    wiki_title = SPECIAL_TITLE_MAP.get(song_name, song_name)
    if song_name not in SPECIAL_TITLE_MAP:
        wiki_title = normalize_title_for_wiki(song_name)

    encoded = urllib.parse.quote(wiki_title, safe='').replace('%20', '_')
    song_page_url = f"https://paradigmrebootzh.miraheze.org/wiki/{encoded}"
    file_direct_url = f"https://paradigmrebootzh.miraheze.org/wiki/文件:Cover_{song_name}.png"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzh.miraheze.org/"
    }

    with httpx.Client(follow_redirects=True) as client:
        try:
            response = client.get(file_direct_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                full_media_div = soup.find("div", class_="fullMedia")
                if full_media_div:
                    img_link = full_media_div.find("a")
                    if img_link and "href" in img_link.attrs:
                        real_url = img_link["href"]
                        if real_url.startswith("//"):
                            real_url = "https:" + real_url
                        return real_url
        except Exception as e:
            pass

        try:
            song_page_response = client.get(song_page_url, headers=headers, timeout=15)
            if song_page_response.status_code != 200:
                print(f"页面 {song_page_url} 访问失败（状态码：{song_page_response.status_code}）")
                return None

            song_soup = BeautifulSoup(song_page_response.text, "html.parser")
            target_img = song_soup.find(
                "img",
                class_="mw-file-element",
                src=lambda x: x and "Cover_" in x
            )
            if not target_img or "src" not in target_img.attrs:
                print(f"页面 {song_page_url} 未找到目标img标签")
                return None

            img_src = target_img["src"]

            if "Cover_" not in img_src:
                print(f"img src {img_src} 不包含 Cover_，无法提取文件名")
                return None

            cover_filename = "Cover_" + img_src.split("Cover_")[1].split("?")[0].split("/")[0]

            if not cover_filename.endswith(".png"):
                cover_filename += ".png"

            restored_file_page_url = f"https://paradigmrebootzh.miraheze.org/wiki/文件:{cover_filename}"
            print(f"尝试文件页面: {restored_file_page_url}")

            file_page_response = client.get(restored_file_page_url, headers=headers, timeout=15)
            if file_page_response.status_code != 200:
                print(f"文件页 {restored_file_page_url} 访问失败（状态码：{file_page_response.status_code}）")
                return None

            file_page_soup = BeautifulSoup(file_page_response.text, "html.parser")
            full_media_div = file_page_soup.find("div", class_="fullMedia")
            if not full_media_div:
                print(f"文件页 {restored_file_page_url} 无 fullMedia 容器")
                return None

            final_img_link = full_media_div.find("a")
            if not final_img_link or "href" not in final_img_link.attrs:
                print(f"文件页 {restored_file_page_url} 无图片链接")
                return None

            final_url = final_img_link["href"]
            if final_url.startswith("//"):
                final_url = "https:" + final_url
            return final_url

        except Exception as e:
            print(f"备用流程执行失败（歌曲：{song_name}），错误：{str(e)}")
            return None


def retry_failed_covers():
    failed_items = [item for item in cover_urls if item["cover_url"] == "获取失败"]
    if not failed_items:
        print("没有获取失败的歌曲需要重试")
        return

    print(f"\n发现 {len(failed_items)} 首歌曲封面获取失败，开始重试...")
    for i, item in enumerate(failed_items, 1):
        song_title = item["title"]
        print(f"正在重试 {i}/{len(failed_items)}：{song_title}")

        new_cover_url = get_cover_url(song_title)
        for entry in cover_urls:
            if entry["title"] == song_title:
                entry["cover_url"] = new_cover_url if new_cover_url else "获取失败"
                break

        if i % 10 == 0 or i == len(failed_items):
            save_results()
            print(f"已临时保存 {len(cover_urls)} 条记录到 cover_url.json")

    print(f"\n重试完成，共处理 {len(failed_items)} 首歌曲，结果已保存")


def main():
    signal.signal(signal.SIGINT, signal_handler)

    if os.path.exists("cover_url.json"):
        try:
            with open("cover_url.json", "r", encoding="utf-8") as f:
                global cover_urls, processed_titles
                cover_urls = json.load(f)
                processed_titles = {item["title"] for item in cover_urls}
                print(f"已加载 {len(cover_urls)} 条历史记录")
        except Exception as e:
            print(f"加载历史记录失败：{str(e)}，将从头开始")

    if not os.path.exists("songs_data.json"):
        print("未找到 songs_data.json 文件，请先准备歌曲数据源！")
        return

    with open("songs_data.json", "r", encoding="utf-8") as f:
        songs_data = json.load(f)

    unique_songs = {}
    for song in songs_data:
        title = song.get("title")
        artist = song.get("artist", "未知歌手")
        if title and title not in unique_songs and title not in processed_titles:
            unique_songs[title] = artist

    total = len(unique_songs)
    if total == 0:
        print("无待处理歌曲（所有歌曲已处理或数据源为空）")
        # 即使没有新歌曲，也检查并重试失败的歌曲
        retry_failed_covers()
        return

    print(f"待处理歌曲总数：{total}\n")
    count = 0

    for song_title, song_artist in unique_songs.items():
        count += 1
        print(f"正在处理 {count}/{total}：{song_title}")

        cover_url = get_cover_url(song_title)

        cover_urls.append({
            "title": song_title,
            "cover_url": cover_url if cover_url else "获取失败",
        })

        if count % 10 == 0 or count == total:
            save_results()
            print(f"已临时保存 {len(cover_urls)} 条记录到 cover_url.json\n")

    print(f"所有歌曲处理完成，共 {len(cover_urls)} 条记录，已保存到cover_url.json")

    # 处理完新歌曲后，重试所有之前获取失败的歌曲
    retry_failed_covers()


if __name__ == "__main__":
    main()
