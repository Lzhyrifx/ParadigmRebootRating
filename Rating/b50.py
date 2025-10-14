from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import os


WIDTH = 1471
CARD_W, CARD_H = 275, 110
COVER_SIZE = 100
PADDING_X, PADDING_Y = 40, 30
SPACING_X, SPACING_Y = 20, 25
FONT_PATH = "res/Source Han Sans Plus Metropolis.otf"
BG_PATH = "res/background.png"
OUTPUT_PATH = "b50_result.png"

DIFFICULTY_COLORS = {
    "massive": (145, 74, 176),
    "invaded": (240, 99, 101),
    "detected": (56, 194, 243)
}

# ============ 工具函数 ============
def load_background():
    bg = Image.open(BG_PATH).convert("RGB")
    w, h = bg.size
    target_ratio = WIDTH / (h / w * WIDTH)
    crop_h = int(w / WIDTH * WIDTH)
    # 自动裁切中心区域
    if w > WIDTH:
        left = (w - WIDTH) // 2
        bg = bg.crop((left, 0, left + WIDTH, h))
    # 模糊处理
    bg = bg.resize((WIDTH, h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=18))
    return bg

def auto_font_size(draw, text, max_width, base_font):
    size = base_font.size
    while size > 10:
        f = ImageFont.truetype(FONT_PATH, size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 1
    return base_font

def draw_card(draw, img, x, y, data, rank):
    diff = data["difficulty"]
    color = DIFFICULTY_COLORS.get(diff, (120, 120, 120))

    # 卡片底
    card = Image.new("RGBA", (CARD_W, CARD_H), color + (255,))
    card_draw = ImageDraw.Draw(card)

    # 封面
    try:
        cover = Image.open(data["cover_path"]).convert("RGBA")
        cover = cover.resize((COVER_SIZE, COVER_SIZE))
    except:
        cover = Image.new("RGBA", (COVER_SIZE, COVER_SIZE), (200, 200, 200, 255))
    card.paste(cover, (5, 5))

    # 文字
    title_font = ImageFont.truetype(FONT_PATH, 28)
    rating_font = ImageFont.truetype(FONT_PATH, 22)
    small_font = ImageFont.truetype(FONT_PATH, 20)
    title_font = auto_font_size(card_draw, data["title"], 140, title_font)

    card_draw.text((115, 5), data["title"], fill="white", font=title_font)
    card_draw.text((115, 40), data["score"], fill="white", font=rating_font)
    card_draw.text((115, 70), f"{data['level']} → {round(data['rating'],3)}", fill="white", font=small_font)
    card_draw.text((CARD_W-40, CARD_H-25), f"#{rank}", fill="white", font=small_font, anchor="rs")

    img.paste(card, (x, y), card)

def draw_section(draw, img, data, title, start_y):
    draw.text((PADDING_X, start_y - 25), title, fill="white", font=ImageFont.truetype(FONT_PATH, 28))
    y = start_y
    x = PADDING_X
    for i, item in enumerate(data):
        draw_card(draw, img, x, y, item, i + 1)
        x += CARD_W + SPACING_X
        if (i + 1) % 5 == 0:
            x = PADDING_X
            y += CARD_H + SPACING_Y
    return y + CARD_H + 40

if __name__ == "__main__":
    with open("songs_results.json", "r", encoding="utf-8") as f:
        js = json.load(f)

    b35 = sorted(js["b35"], key=lambda x: x["rating"], reverse=True)[:35]
    b15 = sorted(js["b15"], key=lambda x: x["rating"], reverse=True)[:15]

    avg35 = round(sum(x["rating"] for x in b35) / len(b35), 2)
    avg15 = round(sum(x["rating"] for x in b15) / len(b15), 2)

    bg = load_background()
    draw = ImageDraw.Draw(bg)

    y = draw_section(draw, bg, b35, f"Best 35 Avg {avg35}", 200)
    draw_section(draw, bg, b15, f"Best 15 Avg {avg15}", y + 50)


    bg.save(OUTPUT_PATH)
    print("生成完毕:", OUTPUT_PATH)
