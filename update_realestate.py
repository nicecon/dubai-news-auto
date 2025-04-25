import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import os
import logging
from openai import OpenAI
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

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
    "launch", "new", "development", "off-plan",
    "residential", "project", "announces", "coming soon"
]

DATE_LIMIT = datetime.now() - timedelta(days=30)
DATE_PATTERN = re.compile(r'(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})')


def summarize_short(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener Immobilienjournalist. Schreibe maximal 2 elegante, professionelle Sätze für ein Neubauprojekt in Dubai. Kein Ort, kein Preis, keine Liste. Nur stilvoller Kurztext."},
                {"role": "user", "content": f"Projektbeschreibung zusammenfassen: {text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.warning(f"⚠️ Fehler bei Zusammenfassung: {e}")
        return text


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
                if not href.startswith("http"):
                    href = url.rstrip("/") + "/" + href.lstrip("/")
                if any(keyword in text.lower() for keyword in PROJECT_KEYWORDS):
                    try:
                        check = requests.head(href, timeout=10)
                        if check.status_code == 200:
                            articles.append({"title": text, "url": href})
                    except:
                        continue
        except Exception as e:
            logging.error(f"❌ Fehler bei {url}: {e}")

    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    return unique[:MAX_ARTICLES]


def format_news(news_items):
    if not news_items:
        return ["**Aktuelle Neubauprojekte in Dubai**\n\nZurzeit liegen keine neuen Meldungen vor."]

    blocks = []
    for item in news_items:
        title = item["title"].strip()
        url = item["url"]
        summary = summarize_short(title)
        block = f"**{title}**\n{summary}\n[Zum Projekt]({url})"
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
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": block, "parse_mode": "Markdown"}
            )
        except Exception as e:
            logging.error(f"❌ Fehler beim Telegram-Senden: {e}")


def main():
    logging.info("🚀 Starte Scraping aktueller Projekte in Dubai")
    news = fetch_project_news()
    blocks = format_news(news)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Projektnews verarbeitet.")

if __name__ == "__main__":
    main()
