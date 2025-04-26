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
    ("off_plan_project", "Nenne ein aktuelles, öffentlich angekündigtes Dubai Off-Plan Immobilienprojekt. Gib Projektname und eine fließende, kurze Beschreibung auf Deutsch, maximal 2 Sätze. Keine Erfindungen, nur reale Projekte.")
]

IMG_WIDTH = 1080
IMG_HEIGHT = 1080
PADDING = 80
TEXT_COLOR = "white"
FONT_BOLD = "fonts/Montserrat-SemiBold.ttf"
LOGO_FILE = "logo.svg"
OUTPUT_DIR = "graphics_offplan"
Path(OUTPUT_DIR).mkdir(exist_ok=True)


def generate_gpt_text(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Du bist Immobilien-Content-Creator. Gib echte, aktuelle Dubai Off-Plan Projekte wieder, sachlich und stilvoll."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


def generate_dalle_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"{prompt}, real photo, natural colors, wide angle, edge-to-edge composition, modern Dubai architecture",
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    img = Image.open(BytesIO(image_data)).resize((IMG_WIDTH, IMG_HEIGHT))
    img = img.filter(ImageFilter.GaussianBlur(radius=8))
    return img


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

    dalle_prompt = f"{content}, modern Dubai off-plan real estate, photorealistic, natural colors"
    bg_img = generate_dalle_image(dalle_prompt)
    bg_img = add_dark_overlay(bg_img)

    draw = ImageDraw.Draw(bg_img)
    title_font = ImageFont.truetype(FONT_BOLD, 90)
    desc_font = ImageFont.truetype(FONT_BOLD, 40)
    link_font = ImageFont.truetype(FONT_BOLD, 25)
    category_font = ImageFont.truetype(FONT_BOLD, 25)

    y = PADDING
    draw.text((PADDING, y), category.upper(), font=category_font, fill=TEXT_COLOR, spacing=4)
    y += draw.textbbox((0, 0), category.upper(), font=category_font)[3] + 20

    # Split Project Name and Description
    if "\n" in content:
        title, description = content.split("\n", 1)
    else:
        title, description = content, ""

    draw.text((PADDING, y), title.strip(), font=title_font, fill=TEXT_COLOR)
    y += draw.textbbox((0, 0), title.strip(), font=title_font)[3] + 20

    if description:
        draw.text((PADDING, y), description.strip(), font=desc_font, fill=TEXT_COLOR)

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
