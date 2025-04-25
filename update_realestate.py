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

MAX_ARTICLES = 15
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Keywords für Neubauprojekte
PROJECT_KEYWORDS = [
    "launch", "dubai", "new", "development", "off-plan",
    "residential", "project", "announces", "coming soon"
]

# Nur Artikel mit Datum innerhalb der letzten 30 Tage
DATE_LIMIT = datetime.now() - timedelta(days=30)
DATE_PATTERN = re.compile(r'(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})')



def translate_text(text):
    logging.info(f"🔁 Übersetze: {text[:80]}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein professioneller deutscher Immobilienredakteur. Übersetze sauber und stilistisch hochwertig."},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content.strip()
        logging.info(f"✅ Übersetzt: {result[:80]}...")
        return result
    except Exception as e:
        logging.error(f"❌ Fehler bei Übersetzung: {e}")
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
    return True  # Wenn kein Datum vorhanden ist, trotzdem anzeigen


def fetch_project_news():
    articles = []
    for url in TARGET_URLS:
        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.content, "html.parser")

            links = soup.find_all("a", href=True)
            for tag in links:
                text = tag.get_text(strip=True)
                if ("dubai" not in text.lower()):
                    continue
                if (any(keyword in text.lower() for keyword in PROJECT_KEYWORDS) and is_recent(text)):
                    href = tag["href"]
                    if not href.startswith("http"):
                        href = url.rstrip("/") + "/" + href.lstrip("/")
                    if not href.lower().startswith("http") or "404" in href:
                        continue
                    articles.append({"title": text, "url": href})
        except Exception as e:
            logging.error(f"❌ Fehler beim Abrufen von {url}: {e}")

    return articles[:MAX_ARTICLES]


def format_news(news_items):
    today = datetime.now(pytz.timezone("Asia/Dubai")).strftime("%d. %B %Y")

    if not news_items:
        return [f"🏗️ Dubai Neubauprojekte – {today}\n\nKeine aktuellen Projektankündigungen gefunden."]

    blocks = [f"🏗️ Dubai Neubauprojekte – {today}\n"]
    for item in news_items:
        title = translate_text(item["title"])
        link = item["url"]
        blocks.append(f"🔹 {title}\n🔗 {link}\n")

    return blocks


def write_to_file(blocks):
    os.makedirs("news", exist_ok=True)
    with open("news/dubai-neubauprojekte-news.txt", "w", encoding="utf-8") as f:
        f.write("# Diese Datei wurde automatisch generiert\n\n")
        for block in blocks:
            f.write(block + "\n")
        f.write(f"\nGeneriert am: {datetime.now().isoformat()}\n")


def send_to_telegram(blocks):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Telegram-Token oder Chat-ID fehlen")
        return

    for block in blocks:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": block}
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
