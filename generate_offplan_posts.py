import os
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from pathlib import Path
import requests
from io import BytesIO
import cairosvg

# OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

current_year = datetime.now().year

CATEGORIES = [
    ("off_plan_project",
     f"Nenne ein neu angekündigtes oder im Bau befindliches Off-Plan Immobilienprojekt in Dubai. "
     f"Der geplante Fertigstellungstermin muss {current_year} oder später liegen. "
     f"Gib zuerst ausschließlich den Projektnamen, dann ein Zeilenumbruch, dann eine stilvolle fließende Kurzbeschreibung "
     f"(maximal 2 Sätze auf Deutsch), die folgende Informationen enthält: "
     f"1. Eine sehr kurze Beschreibung des Projekts. "
     f"2. Den Namen des Entwicklers (Bauträgers). "
     f"3. Die geplante Fertigstellung. "
     f"Keine Erfindungen, keine veralteten Projekte, keine Stichpunkte, keine Einleitungen, nur korrekte Fakten und fließender Text."
    )
]

IMG_WIDTH = 1080
IMG_HEIGHT = 1080
PADDING = 80
TEXT_COLOR = "white"
FONT_BOLD = "fonts/Montserrat-SemiBold.ttf"
FONT_LIGHT = "fonts/Montserrat-Light.ttf"
LOGO_FILE = "logo.svg"
OUTPUT_DIR = "graphics_offplan"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

def generate_gpt_text(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "Du bist Immobilien-Content-Creator für Dubai. "
                "Gib ein echtes aktuelles Off-Plan Projekt wieder: "
                "Zuerst nur der Projektnamen (ohne Zusatz), dann ein Zeilenumbruch, dann eine stilvolle Kurzbeschreibung (max. 2 Sätze) "
                "auf Deutsch, inklusive geplanter Fertigstellung falls verfügbar. "
                "Keine Listen, keine Stichpunkte, keine Einleitungen oder weiteren Kommentare."
            )},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_dalle_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"Photorealistic wide-angle image representing the architecture style of {prompt} project in Dubai, "
               f"matching real building characteristics (without exact copying), natural colors, realistic lighting, soft blur effect, "
               f"edge-to-edge composition, modern skyline background.",
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

def wrap_text(draw, text, font, max_width):
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
    return lines

def draw_wrapped_text(draw, text, font, start_y, max_width, max_height):
    line_spacing = 14  # Hier stellst du deinen festen Zeilenabstand ein (z.B. 8 oder 10)

    lines = wrap_text(draw, text, font, max_width)
    y = start_y
    for l in lines:
        text_height = draw.textbbox((0, 0), l, font=font)[3] - draw.textbbox((0, 0), l, font=font)[1]
        if y + text_height > max_height:
            break
        draw.text((PADDING, y), l, font=font, fill=TEXT_COLOR)
        y += text_height + line_spacing
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
    dalle_prompt = content.split("\n")[0]  # Nur der Projekttitel für DALL-E!

    bg_img = generate_dalle_image(dalle_prompt)
    bg_img = add_dark_overlay(bg_img)

    draw = ImageDraw.Draw(bg_img)
    project_font = ImageFont.truetype(FONT_BOLD, 90)
    description_font = ImageFont.truetype(FONT_LIGHT, 40)
    link_font = ImageFont.truetype(FONT_BOLD, 25)
    category_font = ImageFont.truetype(FONT_BOLD, 25)

    y = PADDING

    # Kategorie oben
    draw.text((PADDING, y), category.upper(), font=category_font, fill=TEXT_COLOR, spacing=4)
    y += draw.textbbox((0, 0), category.upper(), font=category_font)[3] + 20

    # Projektname und Beschreibung sauber trennen
    if "\n" in content:
        project_name, description = content.split("\n", 1)
    else:
        parts = content.split("-", 1)
        project_name = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""

    # Projektname groß und schön umbrechen
    max_text_height = IMG_HEIGHT - 200
    y = draw_wrapped_text(draw, project_name, project_font, y, IMG_WIDTH - 2 * PADDING, max_text_height)

    y += 20  # Abstand zwischen Name und Text

    # Beschreibung zeichnen
    if description:
        y = draw_wrapped_text(draw, description, description_font, y, IMG_WIDTH - 2 * PADDING, max_text_height)

    # Telegram-Link unten
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
