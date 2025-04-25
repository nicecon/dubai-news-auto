import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import os
import logging
from openai import OpenAI
import re

# Setup OpenAI API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Nur URLs, die wirklich Dubai-Projekte zeigen
TARGET_URLS = [
    "https://properties.emaar.com/en/latest-launches/",
    "https://www.dp.ae/our-portfolio/latest-projects/",
    "https://meraas.com/en/latest-project-page",
    "https://www.azizidevelopments.com/projects"
]

MAX_ARTICLES = 4
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PROJECT_KEYWORDS = [
    "launch", "dubai", "new", "development", "off-plan",
    "residential", "project", "announces", "coming soon"
]

DATE_LIMIT = datetime.now() - timedelta(days=30)
DATE_PATTERN = re.compile(r'(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})')


def translate_text(text):
    logging.info(f"🔁 Erstelle kurze Zusammenfassung für: {text[:80]}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein professioneller deutscher Immobilienredakteur. Erstelle elegante, präzise Kurzbeschreibungen für Immobilienprojekte in Dubai."},
                {"role": "user", "content": f"Fasse dieses Neubauprojekt in Dubai elegant zusammen: {text}"}
            ]
        )
        result = response.choices[0].message.content.strip()
        logging.info(f"✅ Zusammenfassung erstellt: {result[:80]}...")
        return result
    except Exception as e:
        logging.error(f"❌ Fehler bei Zusammenfassung: {e}")
        return text


def is_recent(text):
    matches = DATE_PATTERN.findall(text)
    for match in matches:
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%y", "%d/%m/%y", "%d-%m-%y"):
            try:
                parsed_date = datetime.strptime(match, fmt)
                if parsed_date > DATE_LIMIT:
                    return True
            except Exception:
                continue
    return True


def fetch_project_news():
    articles = []
    for url in TARGET_URLS:
        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all("a", href=True)
            for tag in links:
                text = tag.get_text(strip=True)
                href = tag["href"]
                if ("dubai" in text.lower() and any(keyword in text.lower() for keyword in PROJECT_KEYWORDS)):
                    if not href.startswith("http"):
                        href = url.rstrip("/") + "/" + href.lstrip("/")
                    if not any(x in href.lower() for x in ["/project/", "/developments/", "/residences/"]):
                        continue
                    if "404" in href.lower():
                        continue

                    # Hole Projektdetailseite
                    try:
                        proj_resp = requests.get(href, timeout=10)
                        proj_soup = BeautifulSoup(proj_resp.content, "html.parser")
                        image = proj_soup.find("img")
                        image_url = image["src"] if image and "src" in image.attrs else ""
                        location = ""
                        price = ""

                        # Standort & Preis extrahieren
                        for tag_text in proj_soup.stripped_strings:
                            if "location" in tag_text.lower():
                                location = tag_text
                            if any(p in tag_text.lower() for p in ["aed", "price", "from"]):
                                price = tag_text

                        articles.append({
                            "title": text,
                            "url": href,
                            "image": image_url,
                            "location": location,
                            "price": price
                        })
                    except Exception as e:
                        logging.warning(f"⚠️ Detailseite nicht ladbar: {href}")
        except Exception as e:
            logging.error(f"❌ Fehler beim Abrufen von {url}: {e}")

    seen = set()
    unique_articles = []
    for article in articles:
        if article["url"] not in seen:
            unique_articles.append(article)
            seen.add(article["url"])

    return unique_articles[:MAX_ARTICLES]


def format_news(news_items):
    if not news_items:
        return ["Aktuelle Neubauprojekte in Dubai:\n\nKeine aktuellen Projektankündigungen verfügbar."]

    blocks = []
    for item in news_items:
        title = item["title"].strip()
        description = translate_text(title)
        link = item["url"]
        image = item.get("image", "")
        location = item.get("location", "")
        price = item.get("price", "")

        block = f"**{title}**\n"
        if image:
            block += f"![Projektbild]({image})\n"
        if location:
            block += f"📍 {location}\n"
        if price:
            block += f"💰 {price}\n"
        block += f"{description}\n[Zum Projekt]({link})"
        blocks.append(block)

    return blocks


def write_to_file(blocks):
    os.makedirs("news", exist_ok=True)
    with open("news/dubai-neubauprojekte-news.txt", "w", encoding="utf-8") as f:
        f.write("# Diese Datei wurde automatisch generiert\n\n")
        for block in blocks:
            f.write(block + "\n\n")
        f.write(f"Generiert am: {datetime.now().isoformat()}\n")


def send_to_telegram(blocks):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Telegram-Token oder Chat-ID fehlen")
        return

    for block in blocks:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": block, "parse_mode": "Markdown"}
            )
            if response.status_code == 200:
                logging.info("📤 Erfolgreich an Telegram gesendet")
            else:
                logging.error(f"❌ Fehler beim Telegram-Senden: {response.text}")
        except Exception as e:
            logging.error(f"❌ Ausnahme beim Telegram-Versand: {e}")


def main():
    logging.info("🚀 Starte Scraping von Dubai-Projektseiten")
    news = fetch_project_news()
    blocks = format_news(news)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Verarbeitung abgeschlossen.")


if __name__ == "__main__":
    main()
