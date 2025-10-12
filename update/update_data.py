import httpx
import os
import json
import signal
import re
import urllib.parse
import time
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, ConnectionError


COVER_URL_RETRIES = 3


DATA_FILE = "prr_songs_data.json"


SPECIAL_TITLE_MAP = {
    "Cipher : /2&//<|0": "Cipher"
}
DIFFICULTY_LABEL_MAP = {
    "DET": "detected",
    "IVD": "invaded",
    "MSV": "massive"
}



def signal_handler(signal, frame):
    print("\n检测到中断，正在保存已处理数据...")
    if 'songs_data' in globals():
        save_results(songs_data)
        print(f"已保存 {len(songs_data)} 条记录到 {DATA_FILE}")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)



def normalize_title_for_wiki(title: str) -> str:
    return title.replace('[', '［').replace(']', '］').replace('/', '／').replace('#', '＃')



def save_results(songs_data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(songs_data, f, ensure_ascii=False, indent=2)


# 功能函数：提取歌曲封面URL
def get_cover_url(song_name, artist, max_retries=COVER_URL_RETRIES):
    for attempt in range(max_retries):
        try:

            wiki_title = SPECIAL_TITLE_MAP.get(song_name, song_name)
            if song_name not in SPECIAL_TITLE_MAP:
                wiki_title = normalize_title_for_wiki(song_name)


            encoded_title = urllib.parse.quote(wiki_title, safe='').replace('%20', '_')
            song_page_url = f"https://paradigmrebootzh.miraheze.org/wiki/{encoded_title}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Referer": "https://paradigmrebootzh.miraheze.org/"
            }

            with httpx.Client(follow_redirects=True) as client:
                try:
                    song_resp = client.get(song_page_url, headers=headers, timeout=15)
                    if song_resp.status_code != 200:
                        print(f"[{song_name}] 歌曲页访问失败 (状态码: {song_resp.status_code})")
                        continue

                    song_soup = BeautifulSoup(song_resp.text, "html.parser")
                    target_img = song_soup.find(
                        "img",
                        class_="mw-file-element",
                        src=lambda x: x and "Cover_" in x
                    )


                    if not target_img or "src" not in target_img.attrs:
                        safe_artist = artist.replace(' ', '_')
                        artist_title = normalize_title_for_wiki(f"{song_name} ({safe_artist})")
                        encoded_artist_title = urllib.parse.quote(artist_title, safe='').replace('%20', '_')
                        artist_page_url = f"https://paradigmrebootzh.miraheze.org/wiki/{encoded_artist_title}"

                        artist_resp = client.get(artist_page_url, headers=headers, timeout=15)
                        if artist_resp.status_code == 200:
                            artist_soup = BeautifulSoup(artist_resp.text, "html.parser")
                            target_img = artist_soup.find(
                                "img",
                                class_="mw-file-element",
                                src=lambda x: x and "Cover_" in x
                            )

                    if not target_img or "src" not in target_img.attrs:
                        print(f"[{song_name}] 未找到封面图片标签")
                        continue


                    img_src = target_img["src"]

                    cover_filename = "Cover_" + img_src.split("Cover_")[1].split("?")[0].split("/")[0]
                    if not cover_filename.endswith(".png"):
                        cover_filename += ".png"

                    file_page_url = f"https://paradigmrebootzh.miraheze.org/wiki/文件:{cover_filename}"
                    file_resp = client.get(file_page_url, headers=headers, timeout=15)
                    if file_resp.status_code != 200:
                        print(f"[{song_name}] 封面文件页访问失败 (状态码: {file_resp.status_code})")
                        continue

                    file_soup = BeautifulSoup(file_resp.text, "html.parser")
                    full_media = file_soup.find("div", class_="fullMedia")
                    if not full_media or not (final_link := full_media.find("a")) or "href" not in final_link.attrs:
                        print(f"[{song_name}] 封面文件页解析失败")
                        continue

                    final_url = final_link["href"]
                    return "https:" + final_url if final_url.startswith("//") else final_url

                except Exception as e:
                    print(f"[{song_name}] 歌曲页解析失败: {str(e)}")

        except Exception as e:
            print(f"[{song_name}] 第{attempt + 1}次尝试失败: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)

    return "获取失败"



def extract_song_info(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")


        title_elem = soup.find("h1", class_="firstHeading")
        title = title_elem.text.strip() if title_elem else "未知标题"


        artist = "未知艺术家"
        data_full_div = soup.find("div", class_="data full")
        if data_full_div and (artist_a := data_full_div.find("a")):
            artist = artist_a.text.strip()
        else:
            # 备选方案：信息框
            infobox = soup.find("table", class_="infobox")
            if infobox:
                for row in infobox.find_all("tr"):
                    if (th := row.find("th")) and "艺术家" in th.text:
                        if (td := row.find("td")):
                            artist = td.text.strip()
                            break

        # 提取难度定数
        charts = {v: {"level": None} for v in DIFFICULTY_LABEL_MAP.values()}
        label_divs = soup.find_all("div", class_="label")

        for label_div in label_divs:
            # 解析难度标识（如[DET]）
            if not (label_b := label_div.find("b")):
                continue
            label_text = label_b.text.strip()
            if label_text.startswith("[") and label_text.endswith("]"):
                code = label_text[1:-1].upper()
                difficulty_type = DIFFICULTY_LABEL_MAP.get(code)
                if not difficulty_type:
                    continue
            else:
                continue

            # 解析对应定数
            if not (data_div := label_div.find_next_sibling("div", class_="data")):
                continue
            if not (b_elem := data_div.find("b")):
                continue
            integer_part = b_elem.text.strip().replace("+", "").strip()
            if not integer_part.isdigit():
                continue

            if not (small_elem := data_div.find("small")):
                continue
            if not (decimal_match := re.search(r"\.(\d+)", small_elem.text.strip())):
                continue
            decimal_part = decimal_match.group(1)

            # 组合为浮点数
            try:
                charts[difficulty_type]["level"] = float(f"{integer_part}.{decimal_part}")
            except ValueError:
                print(f"[{title}] 定数解析失败: {integer_part}.{decimal_part}")

        return {
            "title": title,
            "artist": artist,
            "b15": True,
            "cover_url": None,
            "charts": charts

        }

    except HTTPError as e:
        print(f"网页访问错误: {str(e)}")
    except ConnectionError as e:
        print(f"网络连接错误: {str(e)}")
    except Exception as e:
        print(f"信息提取错误: {str(e)}")
    return None


def single_data(url, output_file=None):
    """处理单个URL并保存结果"""
    # 先提取歌曲信息，检查是否成功
    song_info = extract_song_info(url)
    if not song_info:
        print(f"[{url}] 提取歌曲信息失败，跳过处理")
        return

    # 检查是否已在数据文件中
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            songs_data = json.load(f)
        # 比较标题判断是否已存在
        if any(song.get("title") == song_info["title"] for song in songs_data):
            print(f"[{url}] 已存在于数据中，跳过")
            return

    # 获取封面
    song_info["cover_url"] = get_cover_url(song_info["title"], song_info["artist"])

    # 保存到数据文件
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            songs_data = json.load(f)
    else:
        songs_data = []
    songs_data.insert(0, song_info)
    save_results(songs_data)

    # 如需单独保存
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(song_info, f, ensure_ascii=False, indent=2)
        print(f"单独保存到 {output_file}")

    print(f"处理完成: {song_info['title']}")


def main():
    global songs_data


    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            songs_data = json.load(f)
    else:
        songs_data = []
        print(f"已创建新数据文件: {DATA_FILE}")


    input_str = input("请输入URL（多个用逗号分隔）: ").strip()

    target_urls = [url.strip() for url in input_str.split(',') if url.strip()]

    for url in target_urls:

        song_info = extract_song_info(url)
        if song_info:
            songs_data.append(song_info)
            print(f"已提取: {song_info['title']} - {song_info['artist']}")
        else:
            print(f"[{url}] 提取失败")


    print("\n开始获取封面URL...")
    total = len(songs_data)
    for i, song in enumerate(songs_data):
        if song.get("cover_url") in (None, "获取失败"):
            print(f"处理封面 ({i + 1}/{total}): {song['title']}")
            song["cover_url"] = get_cover_url(song["title"], song["artist"])


        if (i + 1) % 10 == 0 or i + 1 == total:
            save_results(songs_data)
            print(f"已保存进度 ({i + 1}/{total})")

    print(f"\n所有处理完成，结果已保存到 {DATA_FILE}")


def process_urls_from_input():
    input_str = input("请输入URL（多个用逗号分隔）: ").strip()
    target_urls = [url.strip() for url in input_str.split(',') if url.strip()]

    if not target_urls:
        print("未输入有效URL")
        return

    for url in target_urls:
        single_data(url)

    print(f"\n所有URL处理完成，结果已保存到 {DATA_FILE}")


if __name__ == "__main__":
    process_urls_from_input()