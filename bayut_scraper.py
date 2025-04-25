# bayut_scraper.py

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import logging
import pytz

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

OUTPUT_FILE = "news/dubai-bayut-projects.txt"

async def scrape_bayut_projects():
    projects = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        page = await context.new_page()
        await page.goto("https://www.bayut.com/new-projects/uae/", timeout=90000)

        # Warten, bis Listings erscheinen
        await page.wait_for_selector('li[class*=styles_projectCard]', timeout=60000)

        listings = await page.query_selector_all('li[class*=styles_projectCard]')

        for listing in listings:
            name_element = await listing.query_selector("h2")
            location_element = await listing.query_selector("div:has-text(\"Dubai\")")
            link_element = await listing.query_selector("a")

            if name_element and location_element and link_element:
                name = (await name_element.inner_text()).strip()
                location = (await location_element.inner_text()).strip()
                href = await link_element.get_attribute("href")
                if href and not href.startswith("http"):
                    href = "https://www.bayut.com" + href

                projects.append({
                    "title": f"{name} – {location}",
                    "url": href
                })

        await browser.close()

    return projects

def write_to_file(projects):
    os.makedirs("news", exist_ok=True)
    today = datetime.now(pytz.timezone("Asia/Dubai")).strftime("%d. %B %Y")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Diese Datei wurde automatisch generiert\n\n")
        if not projects:
            f.write(f"Dubai Bayut Projekte – {today}\n\nKeine neuen Projekte gefunden.\n")
        else:
            for project in projects:
                f.write(f"Dubai Bayut Projekte – {today}\n\n{project['title']}\n{project['url']}\n\n")
        f.write(f"Generiert am: {datetime.now().isoformat()}\n")

async def main():
    logging.info("🚀 Starte Playwright Scraping Bayut...")
    projects = await scrape_bayut_projects()
    write_to_file(projects)
    logging.info("✅ Bayut Projekte gespeichert.")

if __name__ == "__main__":
    asyncio.run(main())
