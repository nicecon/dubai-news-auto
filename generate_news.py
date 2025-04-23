import feedparser
from datetime import datetime
import pytz
from html.parser import HTMLParser
import re
import os
import logging
from openai import OpenAI

# 🔐 OpenAI-Client mit modernem Interface (ab Version 1.0.0)
client = OpenAI(api_key="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")  # ⬅️ Hier echten Key eintragen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

RSS_FEEDS = [
    "https://www.thenationalnews.com/page/-/rss/dubai",
    "https://gulfnews.com/rss?path=/uae",
    "https://www.arabianbusiness.com/feed"
]

MAX_ARTICLES = 3

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
                {"role": "system", "content": "Übersetze den folgenden Text professionell ins Deutsche."},
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
        block = f"Dubai-News – {today}\n\n{i}. {title}\n{summary}\n{link}"
        blocks.append(block)

    return blocks

def write_to_file(blocks):
    with open("news/dubai-news.txt", "w", encoding="utf-8") as f:
        f.write("# This file was auto-generated\n\n")
        for block in blocks:
            f.write(block + "\n\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n")

def main():
    logging.info("🚀 Starte News-Aktualisierung")
    print("✅ Logging aktiviert")
    news = fetch_news()
    blocks = format_news(news)
    write_to_file(blocks)
    logging.info("✅ Datei aktualisiert.")

if __name__ == "__main__":
    main()
