import feedparser
from datetime import datetime
import pytz
from html.parser import HTMLParser
import os
import logging
from openai import OpenAI
import requests

# Setup OpenAI API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Immobilien-spezifische RSS-Feeds
RSS_FEEDS = [
    "https://realiste.ai/cities/uae-dubai/c/sqa-real-estate-rss-feeds",
    "https://dubai.savills.ae/footer/rss-feeds.aspx",
    "https://www.dubaichronicle.com/news-feeds/"
]

# Keywords für Neubauprojekte und Entwicklungen
PROJECT_KEYWORDS = [
    "new project", "new development", "launched", "launch", "off-plan", 
    "master development", "under construction", "breaking ground", 
    "phase one", "groundbreaking", "handover", "luxury tower", 
    "community launch", "first phase unveiled", "ready projects", 
    "upcoming projects", "project pipeline", "new communities"
]

MAX_ARTICLES = 5
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class FigureRemovingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_figure = False
        self.output = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "figure":
            self.in_figure = True

    def handle_endtag(self, tag):
        if tag.lower() == "figure":
            self.in_figure = False

    def handle_data(self, data):
        if not self.in_figure:
            self.output.append(data)

    def get_clean_text(self):
        return ''.join(self.output).strip()

def strip_html(raw_html):
    parser = FigureRemovingParser()
    parser.feed(raw_html)
    return parser.get_clean_text()

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

def matches_keywords(entry):
    text = ' '.join([
        entry.get("title", ""),
        entry.get("description", ""),
        entry.get("summary", ""),
        ' '.join([c.get("value", "") for c in entry.get("content", [])]) if "content" in entry else ""
    ]).lower()
    return any(keyword in text for keyword in PROJECT_KEYWORDS)

def fetch_project_news():
    entries = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        entries.extend(feed.entries)

    project_news = [entry for entry in entries if matches_keywords(entry)]
    project_news.sort(key=lambda x: x.get("published_parsed"), reverse=True)
    return project_news[:MAX_ARTICLES]

def format_news(news_items):
    today = datetime.now(pytz.timezone("Asia/Dubai")).strftime("%d. %B %Y")

    if not news_items:
        return [f"Dubai Neubauprojekte-News – {today}\n\nKeine neuen Projekte gemeldet."]

    blocks = []
    for item in news_items:
        title = translate_text(item.title.strip())
        link = item.link.strip()
        summary_raw = item.get("summary", "").strip()
        if not summary_raw and "content" in item and len(item["content"]) > 0:
            summary_raw = item["content"][0].get("value", "")
        summary = translate_text(strip_html(summary_raw))

        block = f"Dubai Neubauprojekte-News – {today}\n\n{title}\n{summary}\n{link}"
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
    logging.info("🚀 Starte Neubauprojekt-News-Aktualisierung")
    news = fetch_project_news()
    blocks = format_news(news)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Verarbeitung abgeschlossen.")

if __name__ == "__main__":
    main()
