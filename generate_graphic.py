import os
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
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

# Alte Bilder löschen
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
        lines = [line.strip() for line in lines if line.strip()]
        blocks.append(lines)
    return blocks

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        width = draw.textlength(test_line, font=font)
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def draw_multiline(draw, lines, font, start_y):
    y = start_y
    for line in lines:
        draw.text((PADDING, y), line, font=font, fill=TEXT_COLOR)
        y += font.getbbox(line)[3] + 10
    return y + 10

def create_image(block_lines, index):
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    date_font = ImageFont.truetype(FONT_LIGHT, 20)
    title_font = ImageFont.truetype(FONT_BOLD, 60)
    body_font = ImageFont.truetype(FONT_LIGHT, 40)

    y = PADDING

    date_line = block_lines[0]
    draw.text((PADDING, y), f"Dubai-News – {date_line}", font=date_font, fill=TEXT_COLOR)
    y += date_font.getbbox(date_line)[3] + 30

    if len(block_lines) > 1:
        headline = re.sub(r"^\d+\.\s*", "", block_lines[1])
        headline_lines = wrap_text(draw, headline, title_font, IMG_WIDTH - 2 * PADDING)
        y = draw_multiline(draw, headline_lines, title_font, y)

    for line in block_lines[2:]:
        if not line.startswith("http") and not line.lower().startswith("generated at"):
            body_lines = wrap_text(draw, line, body_font, IMG_WIDTH - 2 * PADDING)
            y = draw_multiline(draw, body_lines, body_font, y)

    png_logo_path = os.path.join(OUTPUT_DIR, f"logo_tmp_{index}.png")
    cairosvg.svg2png(url=LOGO_FILE, write_to=png_logo_path, output_width=220)
    logo = Image.open(png_logo_path).convert("RGBA")
    img.paste(logo, (IMG_WIDTH - logo.width - 40, IMG_HEIGHT - logo.height - 40), logo)
    os.remove(png_logo_path)

    output_path = os.path.join(OUTPUT_DIR, f"news_{index + 1}.png")
    img.save(output_path)
    print(f"✅ Grafik gespeichert: {output_path}")

def main():
    print("📰 Lese Nachrichten aus Datei...")
    blocks = read_news_blocks()
    for i, block in enumerate(blocks):
        create_image(block, i)

if __name__ == "__main__":
    main()
