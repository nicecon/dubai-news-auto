import feedparser
from datetime import datetime
import pytz
from html.parser import HTMLParser
import re
import os
import logging
from openai import OpenAI
import requests

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

RSS_FEEDS = [
    "https://www.thenationalnews.com/page/-/rss/dubai",
    "https://gulfnews.com/rss?path=/uae",
    "https://www.arabianbusiness.com/feed",
    "https://www.khaleejtimes.com/feed"
]

MAX_ARTICLES = 3
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BREAKING_KEYWORDS = ["breaking", "explosion", "fire", "accident", "urgent", "emergency", "critical"]

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
                {"role": "system", "content": "Du bist ein professioneller deutscher Nachrichtenredakteur. Übersetze präzise und stilistisch einwandfrei."},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content.strip()
        logging.info(f"✅ Übersetzt: {result[:80]}...")
        return result
    except Exception as e:
        logging.error(f"❌ Fehler bei Übersetzung: {e}")
        return text

def fetch_news():
    entries = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        entries.extend(feed.entries)

    dubai_news = [
        entry for entry in entries
        if "dubai" in entry.title.lower() or "dubai" in entry.get("description", "").lower()
    ]

    dubai_news.sort(key=lambda x: x.get("published_parsed"), reverse=True)
    return dubai_news[:MAX_ARTICLES]

def filter_breaking_news(news_items):
    return [
        item for item in news_items
        if any(keyword in item.title.lower() for keyword in BREAKING_KEYWORDS)
    ]

def format_news(news_items):
    today = datetime.now(pytz.timezone("Asia/Dubai")).strftime("%d. %B %Y")

    if not news_items:
        return [f"Dubai-News – {today}\n\nKeine relevanten Dubai-News in den letzten 24 Stunden."]

    blocks = []
    for i, item in enumerate(news_items, start=1):
        title = translate_text(item.title.strip())
        link = item.link.strip()
        summary_raw = item.get("summary", "").strip()
        if not summary_raw and "content" in item and len(item["content"]) > 0:
            summary_raw = item["content"][0].get("value", "")
        summary = translate_text(strip_html(summary_raw))
        prefix = "🚨 BREAKING: " if any(keyword in title.lower() for keyword in BREAKING_KEYWORDS) else f"{i}. "
        block = f"Dubai-News – {today}\n\n{prefix}{title}\n{summary}\n{link}"
        blocks.append(block)

    return blocks

def write_to_file(blocks):
    with open("news/dubai-news.txt", "w", encoding="utf-8") as f:
        f.write("# This file was auto-generated\n\n")
        for block in blocks:
            f.write(block + "\n\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n")

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
                logging.info("📤 Gesendet an Telegram")
            else:
                logging.error(f"❌ Fehler beim Senden an Telegram: {response.text}")
        except Exception as e:
            logging.error(f"❌ Ausnahme bei Telegram-Sendung: {e}")

def main():
    logging.info("🚀 Starte News-Aktualisierung")
    news = fetch_news()

    if os.getenv("ONLY_BREAKING") == "true":
        news = filter_breaking_news(news)
        if not news:
            logging.info("ℹ️ Keine neuen Breaking News gefunden.")
            return

    blocks = format_news(news)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Datei aktualisiert und Telegram-Benachrichtigung gesendet.")

if __name__ == "__main__":
    main()
