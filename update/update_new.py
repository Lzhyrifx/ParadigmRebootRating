import httpx
import urllib.parse
from bs4 import BeautifulSoup
from update_data import single_data  # 导入原有脚本中的single_data函数


def get_new_songs_urls(base_url, target_section="新谱速递"):
    """从指定页面提取新谱速递部分的歌曲URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://paradigmrebootzh.miraheze.org/"
    }

    try:
        # 使用Client处理重定向
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(base_url, headers=headers, timeout=15)
            response.raise_for_status()

            actual_url = str(response.url)
            soup = BeautifulSoup(response.text, "html.parser")

            # 直接查找id为"新谱速递"的锚点所在的h3标题
            target_span = soup.find("span", id=".E6.96.B0.E8.B0.B1.E9.80.9F.E9.80.92")
            if not target_span or not (target_h3 := target_span.find_parent("h3")):
                print(f"未找到'{target_section}'部分")
                return []

            # 找到h3所在的block容器
            block_div = target_h3.find_parent("div", class_="block")
            if not block_div:
                print("未找到包含新谱速递的block容器")
                return []

            # 提取block容器内所有ul中的a标签（针对你提供的HTML结构）
            song_urls = []
            for ul in block_div.find_all("ul"):
                for a_tag in ul.find_all("a", href=True):
                    # 确保是歌曲页面链接
                    if a_tag["href"].startswith("/wiki/"):
                        full_url = urllib.parse.urljoin(actual_url, a_tag["href"])
                        song_urls.append(full_url)

            # 去重处理
            song_urls = list(set(song_urls))
            print(f"成功提取{len(song_urls)}首新谱速递歌曲URL")
            return song_urls

    except Exception as e:
        print(f"提取URL时发生错误: {str(e)}")
        return []


if __name__ == "__main__":

    BASE_WIKI_URL = "https://paradigmrebootzh.miraheze.org/wiki/"


    new_song_urls = get_new_songs_urls(BASE_WIKI_URL)

    if not new_song_urls:
        print("未提取到任何歌曲URL")
    else:
        # 逐个处理每个URL
        for idx, url in enumerate(new_song_urls, 1):
            print(f"\n处理第{idx}/{len(new_song_urls)}首: {url}")
            single_data(url)

        print("\n所有新谱速递歌曲处理完成")