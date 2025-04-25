import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import logging
from openai import OpenAI

# Setup OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Konfiguration - NEUE Immobilien-News-Seiten
TARGET_URLS = [
    "https://gulfnews.com/business/property",
    "https://www.thenationalnews.com/business/property",
    "https://www.arabianbusiness.com/industries/real-estate",
    "https://www.khaleejtimes.com/business/real-estate"
]

MAX_PROJECTS = 4
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def summarize_text(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist Immobilienjournalist. Schreibe maximal 2 elegante Sätze über ein neues Immobilienprojekt in Dubai."},
                {"role": "user", "content": f"Kurzbeschreibung: {text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"❌ Fehler bei OpenAI: {e}")
        return text

def fetch_projects():
    projects = []

    for base_url in TARGET_URLS:
        try:
            resp = requests.get(base_url, timeout=20)
            soup = BeautifulSoup(resp.content, "html.parser")
            links = soup.find_all("a", href=True)

            for link in links:
                title = link.get_text(strip=True)
                href = link["href"]
                if not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")

                if len(title) < 10:
                    continue

                try:
                    check = requests.head(href, timeout=10)
                    if check.status_code == 200:
                        projects.append({"title": title, "url": href})
                except:
                    continue

        except Exception as e:
            logging.error(f"❌ Fehler bei {base_url}: {e}")

    seen = set()
    unique_projects = []
    for p in projects:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique_projects.append(p)

    return unique_projects[:MAX_PROJECTS]

def format_projects(projects):
    blocks = []
    for p in projects:
        title = p["title"]
        url = p["url"]
        short_summary = summarize_text(title)
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
    logging.info("🚀 Starte Immobilien-News Scraping...")
    projects = fetch_projects()
    blocks = format_projects(projects)
    write_to_file(blocks)
    send_to_telegram(blocks)
    logging.info("✅ Update abgeschlossen.")

if __name__ == "__main__":
    main()
