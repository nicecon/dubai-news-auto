import os
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from pathlib import Path
import requests
from io import BytesIO
import cairosvg

# OpenAI Client mit API-Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Kategorien und zugehörige Prompts
CATEGORIES = [
    ("hidden_gem", "Gib mir einen geheimen Ort in Dubai als Instagram-Tipp. Antworte mit maximal einem sehr kurzen Satz (unter 20 Wörtern)."),
    ("lifehack", "Gib mir einen praktischen Lifehack für das Leben in Dubai. Antworte mit maximal einem sehr kurzen Satz (unter 20 Wörtern)."),
    ("event", "Gib mir ein Event in Dubai im April 2025, das interessant ist. Antworte mit maximal einem sehr kurzen Satz (unter 20 Wörtern)."),
    ("fun_fact", "Gib mir einen kuriosen, wenig bekannten Fakt über Dubai. Antworte mit maximal einem sehr kurzen Satz (unter 20 Wörtern)."),
    ("quote", "Gib mir ein motivierendes Zitat mit Bezug auf Dubai oder Wüste. Kurz und inspirierend, maximal 20 Wörter.")
]

IMG_WIDTH = 1080
IMG_HEIGHT = 1080
PADDING = 80
TEXT_COLOR = "white"
FONT_BOLD = "fonts/Montserrat-SemiBold.ttf"
LOGO_FILE = "logo.svg"
OUTPUT_DIR = "graphics"
Path(OUTPUT_DIR).mkdir(exist_ok=True)


def generate_gpt_text(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Du bist ein Social-Media-Content-Creator für Dubai. Die Posts müssen extrem kurz, prägnant und ansprechend sein."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


def generate_dalle_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"{prompt}, real photo, natural colors, Dubai",
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    return Image.open(BytesIO(image_data)).resize((IMG_WIDTH, IMG_HEIGHT))


def add_blur(image):
    return image.filter(ImageFilter.GaussianBlur(radius=8))


def draw_text_block(draw, text, font, start_y, max_width, max_height):
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
        if y + draw.textbbox((0, 0), l, font=font)[3] > max_height:
            break
        draw.text((PADDING, y), l, font=font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), l, font=font)[3] + 4
    return y


def add_logo(image, index):
    tmp_logo = f"logo_tmp_{index}.png"
    cairosvg.svg2png(url=LOGO_FILE, write_to=tmp_logo, output_width=220)
    logo = Image.open(tmp_logo).convert("RGBA")
    image.paste(logo, (IMG_WIDTH - logo.width - 40, IMG_HEIGHT - logo.height - 40), logo)
    os.remove(tmp_logo)
    return image


def create_post_image(category, text, index):
    headline = text.strip()

    dalle_prompt = f"{headline}, real photo, natural colors, Dubai"
    bg_img = generate_dalle_image(dalle_prompt)
    bg_img = add_blur(bg_img)

    draw = ImageDraw.Draw(bg_img)
    title_font = ImageFont.truetype(FONT_BOLD, 60)
    link_font = ImageFont.truetype(FONT_BOLD, 25)

    y = PADDING
    max_text_height = IMG_HEIGHT - 200  # Reserviert Platz für Logo und Link
    y = draw_text_block(draw, headline, title_font, y, IMG_WIDTH - 2 * PADDING, max_text_height)

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
