import os

import pymongo
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
FLIPKART = "https://www.flipkart.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TIMEOUT = 15  # seconds, per request

# Flipkart's generated CSS class names. They change often: update here when scraping returns nothing.
SEARCH_RESULT_CLASS = "cPHDOP col-12-12"
PRODUCT_NAME_CLASS = "VU-ZEz"
REVIEW_BOX_CLASS = "RcXBOT"
REVIEWER_CLASS = "_2NsDsF AwS1CA"


def get(url):
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def text_or(default, fn):
    """Run a lookup on the review markup; fall back to `default` if the markup differs."""
    try:
        return fn().text
    except (AttributeError, IndexError, TypeError):
        return default


def parse_review(product, box):
    inner = box.div.div if box.div else None
    return {
        "Product": product,
        "Name": text_or("No Name", lambda: inner.find_all("p", {"class": REVIEWER_CLASS})[0]),
        "Rating": text_or("No Rating", lambda: inner.div.div),
        "CommentHead": text_or("No Comment Heading", lambda: inner.div.p),
        "Comment": text_or("No Customer Comment", lambda: inner.find_all("div", {"class": ""})[0].div),
    }


def scrape(term):
    """Search Flipkart for `term` and return the reviews of every result page."""
    results = get(f"{FLIPKART}/search?q={term}").find_all("div", {"class": SEARCH_RESULT_CLASS})
    reviews = []
    for result in results[2:]:  # the first two blocks are not products
        link = result.find("a")
        if link is None or not link.get("href"):
            continue
        page = get(FLIPKART + link["href"])
        name = page.find("span", {"class": PRODUCT_NAME_CLASS})
        if name is None:
            continue
        reviews += [parse_review(name.text, box) for box in page.find_all("div", {"class": REVIEW_BOX_CLASS})]
    return reviews


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    term = " ".join(request.form["content"].split())  # collapse whitespace
    if not term:
        return render_template("index.html", error="Enter a product name.")
    key = term.lower()  # one MongoDB collection per search term

    try:
        db = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)["crawlerDB"]
        if key in db.list_collection_names():  # already scraped: serve from the cache
            return render_template("results.html", reviews=list(db[key].find()), term=term)
    except pymongo.errors.PyMongoError:
        return render_template("index.html", error="Could not reach MongoDB. Is it running?"), 503

    try:
        reviews = scrape(term)
    except requests.RequestException as e:
        return render_template("index.html", error=f"Could not fetch Flipkart: {e}"), 502

    if reviews:
        db[key].insert_many(reviews)  # insert_many adds `_id` to each dict; the template ignores it
    return render_template("results.html", reviews=reviews, term=term)


if __name__ == "__main__":
    app.run(port=8000, debug=os.environ.get("FLASK_DEBUG") == "1")
