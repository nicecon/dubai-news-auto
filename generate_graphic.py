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

Path(OUTPUT_DIR).mkdir(exist_ok=True)

def read_news_blocks():
    with open(NEWS_FILE, encoding="utf-8") as f:
        content = f.read()

    raw_blocks = content.split("Dubai-News – ")
    blocks = ["Dubai-News – " + b.strip() for b in raw_blocks if b.strip() and not b.startswith("Generated")]
    return blocks

def create_image(block_text, index):
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(FONT_BOLD, 60)
    body_font = ImageFont.truetype(FONT_LIGHT, 40)

    lines = block_text.split("\n")
    y = PADDING

    for i, line in enumerate(lines):
        if i == 0:
            draw.text((PADDING, y), line, font=title_font, fill="black")
            y += draw.textbbox((0, 0), line, font=title_font)[3] + 30
        elif line.strip():
            for wrapped_line in textwrap.wrap(line, width=60):
                draw.text((PADDING, y), wrapped_line, font=body_font, fill="black")
                y += draw.textbbox((0, 0), wrapped_line, font=body_font)[3] + 10
            y += 20

    # Convert and paste SVG logo
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
