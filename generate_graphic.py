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
LINK_TEXT = "Telegram: @deutsche_in_dubai"
LINK_FONT_SIZE = 25
LINE_SPACING = 15  # Einheitlicher Zeilenabstand

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
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        if len(cleaned_lines) >= 3:
            date_line = cleaned_lines[0]
            headline_line = re.sub(r"^\d+\.\s*", "", cleaned_lines[1])
            summary_lines = [line for line in cleaned_lines[2:] if not line.startswith("http") and "generated at" not in line.lower()]
            blocks.append((date_line, headline_line, "\n".join(summary_lines)))
    return blocks

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        width = draw.textlength(test_line, font=font)
        if width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def draw_wrapped_text(draw, text, font, start_y, max_width):
    y = start_y
    for line in wrap_text(draw, text, font, max_width):
        draw.text((PADDING, y), line, font=font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), line, font=font)[3] + LINE_SPACING
    return y + LINE_SPACING

def create_image(date_line, headline, summary_text, index):
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    date_font = ImageFont.truetype(FONT_LIGHT, 20)
    title_font = ImageFont.truetype(FONT_BOLD, 60)
    body_font = ImageFont.truetype(FONT_LIGHT, 40)
    link_font = ImageFont.truetype(FONT_LIGHT, LINK_FONT_SIZE)

    y = PADDING
    draw.text((PADDING, y), f"Dubai-News – {date_line}", font=date_font, fill=TEXT_COLOR)
    y += draw.textbbox((0, 0), f"Dubai-News – {date_line}", font=date_font)[3] + 30

    y = draw_wrapped_text(draw, headline, title_font, y, IMG_WIDTH - 2 * PADDING)
    y += 20  # Abstand zwischen Headline und Fließtext
    y = draw_wrapped_text(draw, summary_text, body_font, y, IMG_WIDTH - 2 * PADDING)

    # Telegram-Link
    link_y = IMG_HEIGHT - 80
    draw.text((PADDING, link_y), LINK_TEXT, font=link_font, fill=TEXT_COLOR)

    # Logo
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
    for i, (date_line, headline, summary) in enumerate(blocks):
        create_image(date_line, headline, summary, i)

if __name__ == "__main__":
    main()
