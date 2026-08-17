"""
Récupère les flux RSS des sources configurées, filtre les articles par
thématique (mots-clés multilingues) et écrit le résultat dans docs/articles.json,
lu ensuite par la page statique.
"""
import json
import re
import sys
from datetime import datetime, timezone

import feedparser
import requests

SOURCES_PATH = "config/sources.json"
THEMES_PATH = "config/themes.json"
OUTPUT_PATH = "docs/articles.json"
MAX_PER_SOURCE = 30
TIMEOUT = 15
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RevueDePresseBot/1.0)"}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clean_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def match_themes(text, themes):
    text_l = f" {text.lower()} "
    matched = []
    for theme_id, cfg in themes.items():
        keywords = (
            cfg.get("keywords_fr", [])
            + cfg.get("keywords_en", [])
            + cfg.get("keywords_es", [])
        )
        if any(kw.lower() in text_l for kw in keywords):
            matched.append(theme_id)
    return matched


def fetch_source(source, themes):
    articles = []
    try:
        resp = requests.get(source["url"], timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as exc:  # on ne bloque jamais tout le run pour une source en panne
        print(f"[WARN] {source['name']}: échec de récupération ({exc})", file=sys.stderr)
        return []

    for entry in feed.entries[:MAX_PER_SOURCE]:
        title = clean_html(entry.get("title", ""))
        summary = clean_html(entry.get("summary", entry.get("description", "")))
        link = entry.get("link", "")
        if not title or not link:
            continue

        themes_matched = match_themes(f"{title} {summary}", themes)
        if not themes_matched:
            continue

        articles.append(
            {
                "title": title,
                "summary": summary[:400],
                "link": link,
                "source": source["name"],
                "lang": source["lang"],
                "country": source["country"],
                "themes": themes_matched,
                "pubDate": entry.get("published", entry.get("updated", "")),
            }
        )
    return articles


def parse_date(article):
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return datetime.strptime(article["pubDate"], fmt)
        except Exception:
            continue
    return datetime.min.replace(tzinfo=timezone.utc)


def main():
    sources = load_json(SOURCES_PATH)
    themes = load_json(THEMES_PATH)

    all_articles = []
    for source in sources:
        if source.get("disabled") or not source.get("url"):
            continue
        all_articles.extend(fetch_source(source, themes))

    all_articles.sort(key=parse_date, reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "themes": {tid: cfg["label"] for tid, cfg in themes.items()},
        "articles": all_articles,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"{len(all_articles)} articles écrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
