# Web Scrapping – Flipkart review scraper

A small Flask app that scrapes customer reviews for a product search on Flipkart, stores them in MongoDB and shows them in a table.

## How it works

1. Enter a product name in the search box.
2. If that search was scraped before, the reviews are served from MongoDB (`crawlerDB`, one collection per search term, case and extra spaces ignored).
3. Otherwise the app searches Flipkart, opens each product page, extracts the reviews with BeautifulSoup, saves them to MongoDB and displays them.

Each review stores: product, reviewer name, rating, comment heading and comment text.

## Setup

Requires Python 3.9+ and a running MongoDB (default `mongodb://localhost:27017/`).

```bash
pip install -r requirements.txt
python flask_app.py
```

Open http://localhost:8000.

| Environment variable | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `FLASK_DEBUG` | off | set to `1` to enable Flask debug mode |

## Project layout

```
flask_app.py        # routes, scraping, MongoDB caching
templates/          # base, search page, results table
static/css/         # styles
requirements.txt
```

## Known limitations

- Flipkart uses generated CSS class names that change from time to time. The selectors are constants at the top of `flask_app.py`; if a search returns no reviews, update them.
- Scraping is sequential, so a search that opens many product pages can take a while.
- Flipkart may rate-limit or block automated requests.

## Disclaimer

For learning purposes only. Automated scraping may violate Flipkart's terms of service; check them and respect `robots.txt` before using this for anything beyond personal study.
