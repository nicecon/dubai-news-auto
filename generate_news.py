import requests
from datetime import datetime, timedelta
import pytz
import os

BING_API_KEY = os.getenv("BING_API_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/news/search"
HEADERS = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
PARAMS = {
    "q": "Dubai",
    "count": 10,
    "sortBy": "Date",
    "mkt": "en-US",
    "originalImg": "true"
}

def get_recent_dubai_news():
    response = requests.get(BING_ENDPOINT, headers=HEADERS, params=PARAMS)
    response.raise_for_status()
    articles = response.json().get("value", [])

    cutoff = datetime.utcnow() - timedelta(days=1)
    recent = [a for a in articles if datetime.strptime(a['datePublished'], "%Y-%m-%dT%H:%M:%SZ") > cutoff]

    return recent[:3]

def format_news(news_items):
    if not news_items:
        return f"Dubai-News – {datetime.now(pytz.timezone('Asia/Dubai')).strftime('%d. %B %Y')}\n\nKeine relevanten Dubai-News in den letzten 24 Stunden."

    lines = [f"Dubai-News – {datetime.now(pytz.timezone('Asia/Dubai')).strftime('%d. %B %Y')}\n"]
    for i, item in enumerate(news_items, start=1):
        title = item['name']
        url = item['url']
        description = item.get('description', '').strip()
        lines.append(f"{i}. {title}\n{description}\n{url}\n")
    return "\n".join(lines).strip()

def write_to_file(content):
    with open("news/dubai-news.txt", "w", encoding="utf-8") as f:
        f.write(content)

def main():
    news_items = get_recent_dubai_news()
    formatted = format_news(news_items)
    write_to_file(formatted)

if __name__ == "__main__":
    main()
