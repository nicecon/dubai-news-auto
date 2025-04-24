import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
import textwrap
import cairosvg

NEWS_FILE = "news/dubai-news.txt"
LOGO_FILE = "logo.svg"
OUTPUT_DIR = "graphics"
FONT_BOLD = "fonts/Montserrat-SemiBold.ttf"
FONT_LIGHT = "fonts/Montserrat-Light.ttf"
IMG_WIDTH = 1080
IMG_HEIGHT = 1080
PADDING = 80
BG_COLOR = "#465456"
TEXT_COLOR = "white"

Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Lösche alte Bilder
for file in Path(OUTPUT_DIR).glob("*.png"):
    file.unlink()

def read_news_blocks():
    with open(NEWS_FILE, encoding="utf-8") as f:
        content = f.read()

    raw_blocks = content.split("Dubai-News – ")
    blocks = []
    for b in raw_blocks:
        b = b.strip()
        if not b or b.startswith("Generated") or b.startswith("#"):
            continue
        lines = b.split("\n")
        cleaned = [line.strip() for line in lines if line.strip()]
        blocks.append("\n".join(cleaned))
    return blocks

def draw_wrapped_text(draw, text, font, start_y, max_width):
    lines = []
    for paragraph in text.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=40)
        lines.extend(wrapped)
    y = start_y
    for line in lines:
        draw.text((PADDING, y), line, font=font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), line, font=font)[3] + 10
    return y + 20

def create_image(block_text, index):
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    date_font = ImageFont.truetype(FONT_LIGHT, 20)
    title_font = ImageFont.truetype(FONT_BOLD, 60)
    body_font = ImageFont.truetype(FONT_LIGHT, 40)

    lines = block_text.strip().split("\n")
    y = PADDING

    # Datum extrahieren
    if lines:
        draw.text((PADDING, y), f"Dubai-News – {lines[0]}", font=date_font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), f"Dubai-News – {lines[0]}", font=date_font)[3] + 30

    # Headline ohne Nummerierung
    if len(lines) > 1:
        headline = lines[1].strip()
        if headline[:2].isdigit() and headline[2:3] == ".":
            headline = headline[3:].strip()
        y = draw_wrapped_text(draw, headline, title_font, y, IMG_WIDTH - 2 * PADDING)

    # Fließtext
    for line in lines[2:]:
        if not line.lower().startswith("http") and "generated at" not in line.lower():
            y = draw_wrapped_text(draw, line, body_font, y, IMG_WIDTH - 2 * PADDING)

    # Logo
    tmp_logo = os.path.join(OUTPUT_DIR, f"logo_tmp_{index}.png")
    cairosvg.svg2png(url=LOGO_FILE, write_to=tmp_logo, output_width=220)
    logo = Image.open(tmp_logo).convert("RGBA")
    img.paste(logo, (IMG_WIDTH - logo.width - 40, IMG_HEIGHT - logo.height - 40), logo)
    os.remove(tmp_logo)

    out_path = os.path.join(OUTPUT_DIR, f"news_{index + 1}.png")
    img.save(out_path)
    print(f"✅ Grafik gespeichert: {out_path}")

def main():
    print("📰 Lese Nachrichten aus Datei...")
    blocks = read_news_blocks()
    for i, block in enumerate(blocks):
        create_image(block, i)

if __name__ == "__main__":
    main()
