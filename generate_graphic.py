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

# Lösche alte Bilder aus dem Output-Ordner
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
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            cleaned_lines.append(line)
        blocks.append("\n".join(cleaned_lines))
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

    lines = block_text.split("\n")
    y = PADDING

    if lines:
        date_line = lines[0].strip()
        draw.text((PADDING, y), f"Dubai-News – {date_line}", font=date_font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), f"Dubai-News – {date_line}", font=date_font)[3] + 30

    if len(lines) > 1:
        headline = lines[1].strip()
        if len(headline) > 2 and headline[0].isdigit() and headline[1] == ".":
            headline = headline[2:].strip()  # Entferne Nummerierung "1."
        y = draw_wrapped_text(draw, headline, title_font, y, IMG_WIDTH - 2 * PADDING)

    for line in lines[2:]:
        line = line.strip()
        if line and not line.startswith("http") and not line.lower().startswith("generated at"):
            y = draw_wrapped_text(draw, line, body_font, y, IMG_WIDTH - 2 * PADDING)

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
