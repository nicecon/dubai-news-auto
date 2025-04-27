import os
import random
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from pathlib import Path
from io import BytesIO
import cairosvg
from bs4 import BeautifulSoup

# OpenAI Client mit API-Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Kategorien und zugehörige Prompts
CATEGORIES = [
    ("hidden_gem", "Nenne einen echten, weniger bekannten Ort in Dubai (abwechslungsreich, nicht wiederholt wie Al Fahidi). Beschreibe ihn in 1-2 stilvollen Sätzen auf Deutsch."),
    ("lifehack", "Nenne einen echten, praktischen Alltagstipp für Expats oder Touristen in Dubai in maximal 2 kurzen Sätzen auf Deutsch."),
    ("event", "Nenne ein großes, reales, wiederkehrendes Event in Dubai (z.B. Shopping Festival, Art Dubai, Design Week, Airshow). Beschreibe es stilvoll auf Deutsch in maximal 2 Sätzen. Keine neuen Termine, keine Jahreszahlen außer historische."),
    ("fun_fact", "Nenne einen echten, überraschenden Fakt über Dubai. Formuliere sachlich auf Deutsch in max. 2 Sätzen."),
    ("quote", "Gib ein echtes, inspirierendes Zitat mit Bezug zu Dubai oder Wüstenflair auf Deutsch wieder.")
]

IMG_WIDTH = 1080
IMG_HEIGHT = 1080
PADDING = 80
TEXT_COLOR = "white"
FONT_BOLD = "fonts/Montserrat-SemiBold.ttf"
LOGO_FILE = "logo.svg"
OUTPUT_DIR = "graphics"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

LINE_SPACING = 7  # Einheitlicher Zeilenabstand kompakter

def scrape_events():
    try:
        url = "https://www.dubaicalendar.com/events"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GPTBot/1.0;)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        events = soup.select(".event-card")
        event_list = []
        for event in events:
            title = event.select_one(".event-title")
            description = event.select_one(".event-description")
            if title and description:
                event_title = title.get_text(strip=True)
                event_description = description.get_text(strip=True)
                event_list.append((event_title, event_description))

        if event_list:
            return random.choice(event_list)
        else:
            raise Exception("Keine Events gefunden.")

    except Exception:
        fallback_events = [
            ("Dubai Shopping Festival", "Eines der größten Festivals für Shopping und Unterhaltung in Dubai."),
            ("Art Dubai", "Die bedeutendste Kunstmesse der Region, die internationale und lokale Künstler zusammenbringt."),
            ("Dubai Design Week", "Eine kreative Plattform für Designer und Innovatoren weltweit."),
            ("Dubai Food Festival", "Feiere Dubais kulinarische Vielfalt mit Veranstaltungen in der ganzen Stadt.")
        ]
        return random.choice(fallback_events)

def generate_gpt_text(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Du bist ein Social-Media-Content-Creator für Dubai. Gib echte, abwechslungsreiche, sachlich richtige Inhalte in stilvollem Deutsch aus."},
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

def add_dark_overlay(image):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 140))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

def draw_text_block(draw, text, font, start_y, max_width, max_height):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        lines.append("")  # Absatz zwischen Blöcken

    y = start_y
    for l in lines:
        if y + draw.textbbox((0, 0), l, font=font)[3] > max_height:
            break
        draw.text((PADDING, y), l, font=font, fill=TEXT_COLOR)
        y += draw.textbbox((0, 0), l, font=font)[3] + LINE_SPACING
    return y

def add_logo(image, index):
    tmp_logo = f"logo_tmp_{index}.png"
    cairosvg.svg2png(url=LOGO_FILE, write_to=tmp_logo, output_width=220)
    logo = Image.open(tmp_logo).convert("RGBA")
    image.paste(logo, (IMG_WIDTH - logo.width - 40, IMG_HEIGHT - logo.height - 40), logo)
    os.remove(tmp_logo)
    return image

def create_post_image(category, text, index):
    content = text.strip().replace("\"", "")

    dalle_prompt = content.split("\n")[0]

    bg_img = generate_dalle_image(dalle_prompt)
    bg_img = add_blur(bg_img)
    bg_img = add_dark_overlay(bg_img)

    draw = ImageDraw.Draw(bg_img)
    title_font = ImageFont.truetype(FONT_BOLD, 60)
    link_font = ImageFont.truetype(FONT_BOLD, 25)
    category_font = ImageFont.truetype(FONT_BOLD, 25)

    y = PADDING

    draw.text((PADDING, y), category.upper(), font=category_font, fill=TEXT_COLOR)
    y += draw.textbbox((0, 0), category.upper(), font=category_font)[3] + 20

    max_text_height = IMG_HEIGHT - 200
    y = draw_text_block(draw, content, title_font, y, IMG_WIDTH - 2 * PADDING, max_text_height)

    draw.text((PADDING, IMG_HEIGHT - 80), "Telegram: @deutsche_in_dubai", font=link_font, fill=TEXT_COLOR)

    bg_img = add_logo(bg_img, index)

    output_path = os.path.join(OUTPUT_DIR, f"{index + 1}_{category}.png")
    bg_img.save(output_path)
    print(f"✅ Bild gespeichert: {output_path}")

def main():
    for i, (category, prompt) in enumerate(CATEGORIES):
        print(f"\n--- Generiere {category} ---")

        if category == "event":
            event_title, event_description = scrape_events()
            gpt_text = f"{event_title}\n{event_description}"
        else:
            gpt_text = generate_gpt_text(prompt)

        create_post_image(category, gpt_text, i)

if __name__ == "__main__":
    main()
