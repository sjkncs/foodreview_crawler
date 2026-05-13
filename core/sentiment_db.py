"""
舆情数据 SQLite 存储层
表: sentiment_articles
"""
from __future__ import annotations
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.sentiment_models import SentimentArticle

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "sentiment.db"


@contextmanager
def _get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_sentiment_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_articles (
                id           TEXT PRIMARY KEY,
                keyword      TEXT NOT NULL,
                source       TEXT NOT NULL,
                title        TEXT NOT NULL,
                url          TEXT NOT NULL,
                snippet      TEXT,
                author       TEXT,
                publish_time TEXT,
                crawl_time   TEXT,
                sentiment    TEXT,
                tags         TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON sentiment_articles(keyword)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source  ON sentiment_articles(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sentiment ON sentiment_articles(sentiment)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crawl_time ON sentiment_articles(crawl_time)")


def upsert_articles(articles: list[SentimentArticle]) -> int:
    """插入或忽略已存在的文章，返回新增数量"""
    if not articles:
        return 0
    inserted = 0
    with _get_conn() as conn:
        for art in articles:
            cur = conn.execute("""
                INSERT OR IGNORE INTO sentiment_articles
                (id, keyword, source, title, url, snippet, author, publish_time, crawl_time, sentiment, tags)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (art.id, art.keyword, art.source, art.title, art.url,
                  art.snippet, art.author, art.publish_time, art.crawl_time,
                  art.sentiment, art.tags))
            inserted += cur.rowcount
    return inserted


def search_articles(
    keyword: str = "",
    source: str = "",
    sentiment: str = "",
    days: int = 0,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    conditions = []
    params: list = []

    if keyword:
        conditions.append("(keyword LIKE ? OR title LIKE ? OR snippet LIKE ?)")
        params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
    if source:
        conditions.append("source = ?")
        params.append(source)
    if sentiment:
        conditions.append("sentiment = ?")
        params.append(sentiment)
    if days > 0:
        cutoff = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conditions.append("crawl_time >= ?")
        params.append(cutoff)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]

    with _get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM sentiment_articles {where} ORDER BY crawl_time DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def count_articles(keyword: str = "", source: str = "", sentiment: str = "") -> int:
    conditions = []
    params: list = []
    if keyword:
        conditions.append("keyword LIKE ?")
        params.append(f"%{keyword}%")
    if source:
        conditions.append("source = ?")
        params.append(source)
    if sentiment:
        conditions.append("sentiment = ?")
        params.append(sentiment)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    with _get_conn() as conn:
        return conn.execute(
            f"SELECT COUNT(*) FROM sentiment_articles {where}", params
        ).fetchone()[0]


def get_sentiment_distribution(keyword: str = "") -> dict:
    where = "WHERE keyword LIKE ?" if keyword else ""
    params = [f"%{keyword}%"] if keyword else []
    with _get_conn() as conn:
        rows = conn.execute(
            f"SELECT sentiment, COUNT(*) as cnt FROM sentiment_articles {where} GROUP BY sentiment",
            params,
        ).fetchall()
    return {r["sentiment"]: r["cnt"] for r in rows}


def get_source_distribution(keyword: str = "") -> dict:
    where = "WHERE keyword LIKE ?" if keyword else ""
    params = [f"%{keyword}%"] if keyword else []
    with _get_conn() as conn:
        rows = conn.execute(
            f"SELECT source, COUNT(*) as cnt FROM sentiment_articles {where} GROUP BY source",
            params,
        ).fetchall()
    return {r["source"]: r["cnt"] for r in rows}


def get_daily_trend(keyword: str = "", days: int = 7) -> list[dict]:
    """按天统计近N天的文章数量"""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    where_kw = "AND keyword LIKE ?" if keyword else ""
    params: list = [cutoff]
    if keyword:
        params.append(f"%{keyword}%")
    with _get_conn() as conn:
        rows = conn.execute(f"""
            SELECT substr(crawl_time, 1, 10) as day, COUNT(*) as cnt
            FROM sentiment_articles
            WHERE crawl_time >= ? {where_kw}
            GROUP BY day ORDER BY day
        """, params).fetchall()
    return [dict(r) for r in rows]


def get_top_tags(keyword: str = "", limit: int = 20) -> list[tuple[str, int]]:
    """统计高频标签"""
    where = "WHERE keyword LIKE ?" if keyword else ""
    params = [f"%{keyword}%"] if keyword else []
    with _get_conn() as conn:
        rows = conn.execute(
            f"SELECT tags FROM sentiment_articles {where}", params
        ).fetchall()
    tag_count: dict[str, int] = {}
    for row in rows:
        for tag in (row["tags"] or "").split(","):
            tag = tag.strip()
            if tag:
                tag_count[tag] = tag_count.get(tag, 0) + 1
    return sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:limit]


def get_all_keywords() -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT keyword FROM sentiment_articles ORDER BY keyword"
        ).fetchall()
    return [r["keyword"] for r in rows]
