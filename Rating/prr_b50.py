from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import json

# 读取 JSON 数据
with open("prr_songs_data.json", "r", encoding="utf-8") as f:
    songs_data = json.load(f)

# 配置画布尺寸（可根据需求调整）
width, height = 1000, 1500
bg_color = (30, 30, 30)  # 背景色
image = Image.new("RGB", (width, height), bg_color)
draw = ImageDraw.Draw(image)

# 加载字体（需提前准备字体文件，这里假设使用 Arial.ttf，也可替换为系统字体）
try:
    font_title = ImageFont.truetype("Arial.ttf", 14)
    font_artist = ImageFont.truetype("Arial.ttf", 12)
    font_level = ImageFont.truetype("Arial.ttf", 10)
except IOError:
    font_title = ImageFont.load_default()
    font_artist = ImageFont.load_default()
    font_level = ImageFont.load_default()

# 绘制“Best 15”区域
draw.text((50, 30), "Best 15", fill="white", font=font_title)
x, y = 50, 60
best_15_songs = [song for song in songs_data if song.get("b15", False)]
for i, song in enumerate(best_15_songs):
    # 下载曲绘
    response = requests.get(song["cover_url"])
    cover = Image.open(BytesIO(response.content))
    # 调整曲绘尺寸
    cover = cover.resize((80, 80))
    image.paste(cover, (x, y))
    # 绘制标题、艺术家、难度
    draw.text((x + 90, y), song["title"], fill="white", font=font_title)
    draw.text((x + 90, y + 20), song["artist"], fill="white", font=font_artist)
    draw.text((x + 90, y + 40), f"Massive: {song['charts']['massive']['level']}", fill="white", font=font_level)
    # 换行（每行 5 首，共 3 行）
    if (i + 1) % 5 == 0:
        x = 50
        y += 120
    else:
        x += 200

# 绘制“Best 35”区域（这里简单示例，可根据实际数据筛选）
draw.text((50, 400), "Best 35", fill="white", font=font_title)
x, y = 50, 430
# 假设取除了b15为True之外的歌曲作为Best 35部分（实际可根据需求筛选）
best_35_songs = [song for song in songs_data if not song.get("b15", False)]
for i, song in enumerate(best_35_songs[:20]):  # 示例取前20首，可根据实际调整
    response = requests.get(song["cover_url"])
    cover = Image.open(BytesIO(response.content))
    cover = cover.resize((80, 80))
    image.paste(cover, (x, y))
    draw.text((x + 90, y), song["title"], fill="white", font=font_title)
    draw.text((x + 90, y + 20), song["artist"], fill="white", font=font_artist)
    draw.text((x + 90, y + 40), f"Massive: {song['charts']['massive']['level']}", fill="white", font=font_level)
    if (i + 1) % 5 == 0:
        x = 50
        y += 120
    else:
        x += 200

# 保存图片
image.save("prr_player_bests.png")