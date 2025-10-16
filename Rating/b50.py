from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import json
import os
from datetime import datetime

WIDTH = 1620
CARD_W, CARD_H = 275, 95
COVER_SIZE = 85
PADDING_X, PADDING_Y = 40, 30
SPACING_X, SPACING_Y = 40, 30
FONT_PATH = "res/Source Han Sans Plus Metropolis.otf"
BG_PATH = "res/background.png"
OUTPUT_PATH = "b50_result.png"

DIFFICULTY_COLORS = {
    "massive": (145, 74, 176),
    "invaded": (240, 99, 101),
    "detected": (56, 194, 243)
}

# ============ 背景加载 ===============
def load_background():
    bg = Image.open(BG_PATH).convert("RGB")
    w, h = bg.size

    crop_ratio = 0.75
    crop_h = int(h * crop_ratio)
    top = (h - crop_h) // 2
    bg = bg.crop((0, top, w, top + crop_h))

    new_h = int(crop_h * (WIDTH / w))
    bg = bg.resize((WIDTH, new_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=12))
    return bg


# ============ 圆角卡片工具 ===============
def round_corners(im, radius):
    """返回带圆角的RGBA图像"""
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, im.size[0], im.size[1]), radius=radius, fill=255)
    im.putalpha(mask)
    return im


# ============ 顶部信息栏 ===============
def draw_header(draw, img, username, avg35, avg15):
    title_font = ImageFont.truetype(FONT_PATH, 40)


    left_title = f"{username}"


    # 新 Rating 计算
    total_rating = (avg35 + avg15) / 2
    right_title = f"Rating: {total_rating:.2f}"


    left_title_y = 120
    right_title_y = 120
    margin_right = 60

    draw.text((60, left_title_y), left_title, fill="white", font=title_font)


    right_title_w = draw.textlength(right_title, font=title_font)


    draw.text((WIDTH - right_title_w - margin_right, right_title_y),
              right_title, fill="white", font=title_font)


# ============ 单张卡片绘制 ===============
def draw_card(draw, img, x, y, data, rank):
    diff = data["difficulty"]
    color = DIFFICULTY_COLORS.get(diff, (120, 120, 120))

    # 创建圆角卡片背景
    card = Image.new("RGBA", (CARD_W, CARD_H), color + (255,))
    card = round_corners(card, radius=15)
    card_draw = ImageDraw.Draw(card)

    # 加载封面
    try:
        cover = Image.open(data["cover_path"]).convert("RGBA")
        cover = cover.resize((COVER_SIZE, COVER_SIZE))
    except:
        cover = Image.new("RGBA", (COVER_SIZE, COVER_SIZE), (200, 200, 200, 255))
    card.paste(cover, (5, 5), cover)

    # 字体设置
    title_font = ImageFont.truetype(FONT_PATH, 24)
    rating_font = ImageFont.truetype("res/Closeness.ttf", 24)
    small_font = ImageFont.truetype(FONT_PATH, 18)

    # 标题过长自动省略
    title = data["title"]
    max_width = 160
    if card_draw.textlength(title, font=title_font) > max_width:
        while card_draw.textlength(title + "...", font=title_font) > max_width and len(title) > 1:
            title = title[:-1]
        title = title + "..."

    # 绘制文字
    card_draw.text((100, 5), title, fill="white", font=title_font)
    card_draw.text((95, 32), data["score"], fill="white", font=rating_font)
    card_draw.text((100, 70), f"{data['level']} → {round(data['rating'], 3)}", fill="white", font=small_font)
    card_draw.text((CARD_W - 10, CARD_H - 10), f"#{rank}", fill="white", font=small_font, anchor="rs")

    # 粘贴到主图
    img.paste(card, (x, y), card)


# ============ 表格区块绘制 ===============
def draw_section(draw, img, data, title, start_y):
    title_font = ImageFont.truetype(FONT_PATH, 28)
    title_y = start_y - 60

    title_w = draw.textlength(title, font=title_font)
    center_x = WIDTH // 2
    title_x = center_x - title_w // 2

    draw.text((title_x, title_y), title, fill="white", font=title_font)

    # 左右横线
    line_margin = 25
    line_y = title_y + title_font.size // 2
    line_len = 615

    draw.line((title_x - line_len - line_margin, line_y, title_x - line_margin, line_y), fill="white", width=3)
    draw.line((title_x + title_w + line_margin, line_y, title_x + title_w + line_margin + line_len, line_y), fill="white", width=3)

    # 卡片绘制
    y = start_y
    x = PADDING_X
    for i, item in enumerate(data):
        draw_card(draw, img, x, y, item, i + 1)
        x += CARD_W + SPACING_X
        if (i + 1) % 5 == 0:
            x = PADDING_X
            y += CARD_H + SPACING_Y

    return y + CARD_H + 60



if __name__ == "__main__":
    with open("songs_results.json", "r", encoding="utf-8") as f:
        js = json.load(f)

    b35 = sorted(js["b35"], key=lambda x: x["rating"], reverse=True)[:35]
    b15 = sorted(js["b15"], key=lambda x: x["rating"], reverse=True)[:15]

    avg35 = round(sum(x["rating"] for x in b35) / len(b35), 2)
    avg15 = round(sum(x["rating"] for x in b15) / len(b15), 2)

    bg = load_background()
    draw = ImageDraw.Draw(bg)

    username = "Lzhyrifx"
    draw_header(draw, bg, username, avg35, avg15)

    y = draw_section(draw, bg, b35, f"Best 35 Avg {avg35}", 310) #430
    draw_section(draw, bg, b15, f"Best 15 Avg {avg15}", y - 75)

    bg.save(OUTPUT_PATH)
    print("生成完毕:", OUTPUT_PATH)
