import os
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from pathlib import Path
import requests
from io import BytesIO
import cairosvg

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = [
    ("hidden_gem", "Nenne einen echten, realen Ort in Dubai, der weniger bekannt, aber öffentlich zugänglich und sehenswert ist. Beschreibe ihn in 1-2 Sätzen auf Deutsch, ohne Übertreibung oder Erfindung."),
    ("lifehack", "Nenne einen echten, praktischen Dubai-Alltagstipp für Expats oder Touristen in maximal 2 kurzen Sätzen auf Deutsch. Keine Erfindungen."),
    ("event", "Nenne ein echtes, öffentlich angekündigtes Event, das demnächst oder regelmäßig in Dubai stattfindet – wie Festivals, Ausstellungen, Konzerte oder Messen. Antworte mit Titel + 1 Satz Beschreibung auf Deutsch. Keine Spekulation. Keine Disclaimer."),
    ("fun_fact", "Nenne einen überprüfbaren Fakt über Dubai, der überraschend ist. Formuliere sachlich auf Deutsch in max. 2 Sätzen."),
    ("quote", "Gib ein inspirierendes Zitat mit Dubai-Bezug oder Wüstenflair wieder – keine Erfindungen, sondern stilvoller, echter Ausdruck.")
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
            {"role": "system", "content": "Du bist Content-Creator für Instagram-Posts über Dubai. Antworte sachlich, kurz, in einem klaren, stilvollen Ton. Keine Übertreibung, keine erfundenen Aussagen."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


def generate_dalle_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"{prompt}, real photo, natural colors, wide angle, no borders, edge-to-edge composition",
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    return Image.open(BytesIO(image_data)).resize((IMG_WIDTH, IMG_HEIGHT))


def add_blur(image):
    return image.filter(ImageFilter.GaussianBlur(radius=6))


def draw_text_block(draw, text, font, start_y, max_width, max_height):
    words = text.replace("\"", "").split()
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
        y += draw.textbbox((0, 0), l, font=font)[3] + 6
    return y


def add_dark_overlay(image):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 140))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def add_logo(image, index):
    tmp_logo = f"logo_tmp_{index}.png"
    cairosvg.svg2png(url=LOGO_FILE, write_to=tmp_logo, output_width=220)
    logo = Image.open(tmp_logo).convert("RGBA")
    image.paste(logo, (IMG_WIDTH - logo.width - 40, IMG_HEIGHT - logo.height - 40), logo)
    os.remove(tmp_logo)
    return image


def create_post_image(category, text, index):
    content = text.strip().replace("\"", "")
    dalle_prompt = f"{content}, real photo, natural colors, wide angle, no borders"
    bg_img = generate_dalle_image(dalle_prompt)
    bg_img = add_blur(bg_img)
    bg_img = add_dark_overlay(bg_img)

    draw = ImageDraw.Draw(bg_img)
    font = ImageFont.truetype(FONT_BOLD, 60)
    link_font = ImageFont.truetype(FONT_BOLD, 25)

    y = PADDING
    max_text_height = IMG_HEIGHT - 200
    y = draw_text_block(draw, content, font, y, IMG_WIDTH - 2 * PADDING, max_text_height)

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
