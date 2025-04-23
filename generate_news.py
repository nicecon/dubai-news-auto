import feedparser
from datetime import datetime
import pytz

RSS_FEEDS = [
    "https://www.thenationalnews.com/page/-/rss/dubai",
    "https://gulfnews.com/rss?path=/uae",
    "https://www.arabianbusiness.com/feed"
]

MAX_ARTICLES = 3

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
        title = item.title.strip()
        link = item.link.strip()
        summary = item.get("summary", "").strip()
        block = f"Dubai-News – {today}\n\n{i}. {title}\n{summary}\n{link}"
        blocks.append(block)

    return blocks

def write_to_file(blocks):
    with open("news/dubai-news.txt", "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(block + "\n\n")

def main():
    news = fetch_news()
    blocks = format_news(news)
    write_to_file(blocks)

if __name__ == "__main__":
    main()
# Trigger change
