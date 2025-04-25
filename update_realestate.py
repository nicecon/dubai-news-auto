import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os
import logging
from openai import OpenAI

# Setup OpenAI API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Ziel-URLs (Seiten, die neue Immobilienprojekte auflisten)
TARGET_URLS = [
    "https://www.propertyfinder.ae/blog/category/news/",
    "https://www.emaar.com/en/what-we-do/residential/new-launch/"
]

MAX_ARTICLES = 5
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Keywords für Neubauprojekte
PROJECT_KEYWORDS = [
    "launch", "new project", "new development", "off-plan", 
    "residential community", "construction started", "unveils", "master plan",
    "announces", "breaks ground", "launching soon", "sales event"
]

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

def fetch_bayut_projects():
    url = "https://www.bayut.com/new-projects/uae/"
    projects = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        listings = soup.select("li[class*=styles_projectCard]")

        for listing in listings:
            name_tag = listing.find("h2")
            location_tag = listing.find("div", string=lambda t: t and "Dubai" in t)
            link_tag = listing.find("a", href=True)

            if name_tag and location_tag and link_tag:
                name = name_tag.get_text(strip=True)
                location = location_tag.get_text(strip=True)
                href = link_tag["href"]
                if not href.startswith("http"):
                    href = "https://www.bayut.com" + href

                projects.append({
                    "title": f"{name} – {location}",
                    "url": href
                })

    except Exception as e:
        logging.error(f"❌ Fehler beim Abrufen von Bayut: {e}")
    return projects

def fetch_project_news():
    articles = fetch_bayut_projects()  # Beginne mit Bayut
    for url in TARGET_URLS:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            headlines = soup.find_all(["h1", "h2", "h3", "a"])
            for tag in headlines:
                text = tag.get_text(strip=True)
                if any(keyword in text.lower() for keyword in PROJECT_KEYWORDS):
                    href = tag.get("href")
                    if href and not href.startswith("http"):
                        href = url.rstrip("/") + "/" + href.lstrip("/")
                    articles.append({"title": text, "url": href or url})
        except Exception as e:
            logging.error(f"❌ Fehler beim Abrufen von {url}: {e}")

    return articles[:MAX_ARTICLES]

def format_news(news_items):
    today = datetime.now(pytz.timezone("Asia/Dubai")).strftime("%d. %B %Y")

    if not news_items:
        return [f"Dubai Neubauprojekte-News – {today}\n\nKeine neuen Projekte gemeldet."]

    blocks = []
    for item in news_items:
        title = translate_text(item["title"])
        link = item["url"]

        block = f"Dubai Neubauprojekte-News – {today}\n\n{title}\n{link}"
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
                data={"chat_id": TELEGRAM_CHAT_ID, "text": block}
            )
            if response.status_code == 200:
                logging.info("📤 Erfolgreich an Telegram gesendet")
            else:
                logging.error(f"❌ Fehler beim Telegram-Senden: {response.text}")
        except Exception as e:
            logging.error(f"❌ Ausnahme beim Telegram-Versand: {e}")

def main():
    logging.info("🚀 Starte Scraping von Neubauprojekten")
    news = fetch_project_news()
    blocks = format_news(news)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Verarbeitung abgeschlossen.")

if __name__ == "__main__":
    main()
