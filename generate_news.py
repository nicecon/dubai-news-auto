import feedparser
from datetime import datetime
import pytz
from html.parser import HTMLParser

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
        elif not self.in_figure:
            pass  # Could handle valid tags here if needed

    def handle_endtag(self, tag):
        if tag.lower() == "figure":
            self.in_figure = False

    def handle_data(self, data):
        if not self.in_figure:
            self.output.append(data)

    def handle_startendtag(self, tag, attrs):
        if not self.in_figure:
            pass  # Only pass through tags outside figure

    def get_clean_text(self):
        return ''.join(self.output).strip()

def strip_html(raw_html):
    parser = FigureRemovingParser()
    parser.feed(raw_html)
    return parser.get_clean_text()

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
        return [f"TEST Dubai-News – {today}\n\nKeine relevanten Dubai-News in den letzten 24 Stunden."]

    blocks = []
    for i, item in enumerate(news_items, start=1):
        title = item.title.strip()
        link = item.link.strip()
        summary_raw = item.get("summary", "").strip()
        if not summary_raw and "content" in item and len(item["content"]) > 0:
            summary_raw = item["content"][0].get("value", "")
        summary = strip_html(summary_raw)
        block = f"TEST Dubai-News – {today}\n\n{i}. {title}\n{summary}\n{link}"
        blocks.append(block)

    return blocks

def write_to_file(blocks):
    with open("news/dubai-news.txt", "w", encoding="utf-8") as f:
        f.write("# This file was auto-generated\n\n")
        for block in blocks:
            f.write(block + "\n\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n")

def main():
    news = fetch_news()
    blocks = format_news(news)
    write_to_file(blocks)

if __name__ == "__main__":
    main()
