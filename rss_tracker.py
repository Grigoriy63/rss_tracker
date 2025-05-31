import sqlite3
import feedparser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time

DB_PATH = "rss_tracker.db"

app = FastAPI()

class RSSSource(BaseModel):
    url: str

class Keyword(BaseModel):
    word: str

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS sources (url TEXT PRIMARY KEY)")
        c.execute("CREATE TABLE IF NOT EXISTS keywords (word TEXT PRIMARY KEY)")
        c.execute("""CREATE TABLE IF NOT EXISTS news (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        summary TEXT,
                        link TEXT,
                        published TEXT
                    )""")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_link ON news(link)")
        conn.commit()

def fetch_and_store_news():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT url FROM sources")
        sources = [row[0] for row in c.fetchall()]
        c.execute("SELECT word FROM keywords")
        keywords = [row[0].lower() for row in c.fetchall()]

        for url in sources:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                text = f"{entry.title} {entry.get('summary', '')}".lower()
                if any(kw in text for kw in keywords):
                    try:
                        c.execute("""INSERT INTO news (title, summary, link, published)
                                     VALUES (?, ?, ?, ?)""",
                                  (entry.title, entry.get("summary", ""), entry.link, entry.get("published", "")))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        continue

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_news, "interval", minutes=15)
scheduler.start()


@app.post("/sources")
def add_source(src: RSSSource):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute("INSERT INTO sources (url) VALUES (?)", (src.url,))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Источник уже существует")
    return {"status": "ok"}

@app.get("/sources")
def list_sources():
    with sqlite3.connect(DB_PATH) as conn:
        return [row[0] for row in conn.execute("SELECT url FROM sources")]

@app.post("/keywords")
def add_keyword(kw: Keyword):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute("INSERT INTO keywords (word) VALUES (?)", (kw.word,))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Ключевое слово уже добавлено")
    return {"status": "ok"}

@app.get("/keywords")
def list_keywords():
    with sqlite3.connect(DB_PATH) as conn:
        return [row[0] for row in conn.execute("SELECT word FROM keywords")]

@app.get("/news", response_class=HTMLResponse)
def get_news():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM news ORDER BY published DESC").fetchall()

        html = """
        <html>
            <head>
                <title>Новости по ключевым словам</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 2em; background-color: #f4f4f4; }
                    .news-item { background: white; padding: 1em; margin-bottom: 1em; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                    .news-title { font-size: 1.2em; margin-bottom: 0.5em; }
                    .news-summary { color: #555; }
                    .news-date { font-size: 0.9em; color: #888; margin-top: 0.5em; }
                </style>
            </head>
            <body>
                <h1>Собранные новости</h1>
        """
        for row in rows:
            html += f"""
                <div class="news-item">
                    <div class="news-title"><a href="{row['link']}" target="_blank">{row['title']}</a></div>
                    <div class="news-summary">{row['summary']}</div>
                    <div class="news-date">{row['published']}</div>
                </div>
            """
        html += "</body></html>"
        return HTMLResponse(content=html)


if __name__ == "__main__":
    init_db()
    uvicorn.run("rss_tracker:app", host="0.0.0.0", port=8000, reload=False)
