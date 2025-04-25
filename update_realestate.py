import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import logging
from urllib.parse import quote_plus

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

MAX_PROJECTS = 5
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GOOGLE_SEARCH_URL = "https://www.google.com/search?q={query}&hl=en&gl=ae"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"
}

SEARCH_QUERY = "Dubai new real estate project launch 2025 site:gulfnews.com OR site:thenationalnews.com OR site:propertyfinder.ae"


def fetch_google_results(query):
    projects = []
    search_url = GOOGLE_SEARCH_URL.format(query=quote_plus(query))
    resp = requests.get(search_url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(resp.content, "html.parser")

    for g_card in soup.select("div.tF2Cxc"):
        title_element = g_card.select_one("h3")
        link_element = g_card.select_one("a")
        if title_element and link_element:
            title = title_element.get_text()
            url = link_element["href"]
            projects.append({"title": title, "url": url})

    return projects[:MAX_PROJECTS]


def format_projects(projects):
    blocks = []
    for p in projects:
        title = p["title"]
        url = p["url"]
        short_summary = f"Neues Projekt: {title}"
        block = f"**{title}**\n{short_summary}\n[Zum Artikel]({url})"
        blocks.append(block)
    return blocks


def write_to_file(blocks):
    os.makedirs("news", exist_ok=True)
    with open("news/dubai-realestate-news.txt", "w", encoding="utf-8") as f:
        f.write("# Diese Datei wurde automatisch generiert\n\n")
        for block in blocks:
            f.write(block + "\n\n")
        f.write(f"Generiert am: {datetime.now().isoformat()}\n")


def send_to_telegram(blocks):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Telegram-Konfiguration fehlt.")
        return

    for block in blocks:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": block, "parse_mode": "Markdown"}
            )
        except Exception as e:
            logging.error(f"❌ Fehler bei Telegram: {e}")


def main():
    logging.info("🚀 Starte Google News Scraping...")
    projects = fetch_google_results(SEARCH_QUERY)
    blocks = format_projects(projects)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Update abgeschlossen.")


if __name__ == "__main__":
    main()
