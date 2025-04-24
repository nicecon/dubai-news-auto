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

def read_news_blocks():
    with open(NEWS_FILE, encoding="utf-8") as f:
        content = f.read()

    raw_blocks = content.split("Dubai-News – ")
    blocks = [b.strip() for b in raw_blocks if b.strip() and not b.startswith("Generated") and not b.startswith("#")]
    return blocks

def create_image(block_text, index):
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    date_font = ImageFont.truetype(FONT_LIGHT, 20)
    title_font = ImageFont.truetype(FONT_BOLD, 60)
    body_font = ImageFont.truetype(FONT_LIGHT, 40)

    lines = block_text.split("\n")
    y = PADDING

    if lines:
        # Draw small date line
        draw.text((PADDING, y), f"Dubai-News – {lines[0].strip()}", font=date_font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), lines[0], font=date_font)[3] + 30

    if len(lines) > 1:
        # Draw headline
        draw.text((PADDING, y), lines[1], font=title_font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), lines[1], font=title_font)[3] + 30

    # Draw remaining body text
    for line in lines[2:]:
        if line.strip() and not line.startswith("http"):
            for wrapped_line in textwrap.wrap(line, width=50):
                draw.text((PADDING, y), wrapped_line, font=body_font, fill=TEXT_COLOR)
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
