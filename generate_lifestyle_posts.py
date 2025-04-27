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
        size="1024x
