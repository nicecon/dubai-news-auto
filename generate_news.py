name: Update Dubai News

on:
  schedule:
    - cron: '0 5 * * *'  # Täglich um 9:00 Uhr Dubai-Zeit (5:00 UTC)
  workflow_dispatch:

jobs:
  update-news:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: python -m pip install feedparser pytz requests

      - name: Run news script
        run: python generate_news.py

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add news/dubai-news.txt
          git commit -m "Daily Dubai News Update" || echo "No changes to commit"
          git push
