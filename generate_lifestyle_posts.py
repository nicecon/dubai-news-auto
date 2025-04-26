
import os
import openai
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
import requests
from io import BytesIO
import cairosvg

# OpenAI API Key aus Umgebungsvariable (GitHub Secret)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Kategorien und zugehörige Prompts
CATEGORIES = [
    ("hidden_gem", "Gib mir einen geheimen Ort in Dubai als Instagram-Tipp. Kurzbeschreibung auf Deutsch."),
    ("lifehack", "Gib mir einen praktischen Lifehack für das Leben in Dubai. Kurzbeschreibung auf Deutsch."),
    ("event", "Gib mir ein Event in Dubai im April 2025, das interessant ist. Kurzbeschreibung auf Deutsch."),
    ("fun_fact", "Gib mir einen kuriosen, wenig bekannten Fakt über Dubai. Kurzbeschreibung auf Deutsch."),
    ("quote", "Gib mir ein motivierendes Zitat mit Bezug auf Dubai oder Wüste. Kurz und inspirierend auf Deutsch.")
]

IMG_WIDTH = 1080
IMG_HEIGHT = 1080
PADDING = 80
BG_OVERLAY = (0, 0, 0, 100)
TEXT_COLOR = "white"
FONT_BOLD = "fonts/Montserrat-SemiBold.ttf"
FONT_LIGHT = "fonts/Montserrat-Light.ttf"
LOGO_FILE = "logo.svg"
OUTPUT_DIR = "graphics"
Path(OUTPUT_DIR).mkdir(exist_ok=True)


def generate_gpt_text(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Du bist ein Social-Media-Content-Creator für Dubai."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


def generate_dalle_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    image_data = requests.get(image_url).content
    return Image.open(BytesIO(image_data)).resize((IMG_WIDTH, IMG_HEIGHT))


def draw_text_block(draw, text, font, start_y, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if draw.textlength(test_line, font=font) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    y = start_y
    for l in lines:
        draw.text((PADDING, y), l, font=font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), l, font=font)[3] + 10
    return y


def add_overlay(image):
    overlay = Image.new("RGBA", image.size, BG_OVERLAY)
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def add_logo(image, index):
    tmp_logo = f"logo_tmp_{index}.png"
    cairosvg.svg2png(url=LOGO_FILE, write_to=tmp_logo, output_width=220)
    logo = Image.open(tmp_logo).convert("RGBA")
    image.paste(logo, (IMG_WIDTH - logo.width - 40, IMG_HEIGHT - logo.height - 40), logo)
    os.remove(tmp_logo)
    return image


def create_post_image(category, text, index):
    headline, *rest = text.split("\n")
    summary = " ".join(rest).strip()

    dalle_prompt = f"Fotorealistisches Bild zu: {headline}. Dubai, Stimmungsvoll, Farbenfroh."
    bg_img = generate_dalle_image(dalle_prompt)
    bg_img = add_overlay(bg_img)

    draw = ImageDraw.Draw(bg_img)
    date_str = datetime.now().strftime("%d. %B %Y")
    date_font = ImageFont.truetype(FONT_LIGHT, 24)
    title_font = ImageFont.truetype(FONT_BOLD, 58)
    body_font = ImageFont.truetype(FONT_LIGHT, 40)
    link_font = ImageFont.truetype(FONT_LIGHT, 25)

    y = PADDING
    draw.text((PADDING, y), f"Dubai-News – {date_str}", font=date_font, fill=TEXT_COLOR)
    y += draw.textbbox((0, 0), f"Dubai-News – {date_str}", font=date_font)[3] + 30
    y = draw_text_block(draw, headline, title_font, y, IMG_WIDTH - 2 * PADDING)
    y += 20
    y = draw_text_block(draw, summary, body_font, y, IMG_WIDTH - 2 * PADDING)

    draw.text((PADDING, IMG_HEIGHT - 80), "Telegram: @deutsche_in_dubai", font=link_font, fill=TEXT_COLOR)
    bg_img = add_logo(bg_img, index)

    output_path = os.path.join(OUTPUT_DIR, f"{index + 1}_{category}.png")
    bg_img.save(output_path)
    print(f"✅ Bild gespeichert: {output_path}")


def main():
    for i, (category, prompt) in enumerate(CATEGORIES):
        print(f"\n--- Generiere {category} ---")
        gpt_text = generate_gpt_text(prompt)
        create_post_image(category, gpt_text, i)


if __name__ == "__main__":
    main()
