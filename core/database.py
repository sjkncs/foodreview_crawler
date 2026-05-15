"""
SQLite 数据库层 - Repository Pattern
新增字段：translated_content, published_at, image_urls,
          merchant_reply, reply_translation, child_rating, page_url, ocr_strategy
"""
from __future__ import annotations
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from .models import CrawlTask, Platform, Review, ReviewType, SentimentLabel, Shop

DB_PATH = Path(__file__).parent.parent / "data" / "reviews.db"


def _ensure_db_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _get_conn() -> Generator[sqlite3.Connection, None, None]:
    _ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """初始化/迁移数据库表结构"""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS shops (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                platform      TEXT NOT NULL,
                shop_id       TEXT NOT NULL,
                name          TEXT NOT NULL,
                category      TEXT,
                address       TEXT,
                rating        REAL,
                review_count  INTEGER DEFAULT 0,
                registered_at TEXT,
                extra         TEXT,
                UNIQUE(platform, shop_id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                -- 表单主字段（与表头一一对应）
                platform            TEXT NOT NULL,       -- 平台
                shop_name           TEXT NOT NULL,       -- 店铺名称
                shop_id             TEXT NOT NULL,
                reviewer_name       TEXT,                -- 用户名
                content             TEXT NOT NULL,       -- 评论内容
                rating              REAL,                -- 评分
                translated_content  TEXT,                -- 翻译内容
                published_at        TEXT,                -- 发布日期（原始时间）
                crawled_at          TEXT NOT NULL,       -- 采集时间
                image_urls          TEXT,                -- 图片URLs（JSON数组）
                merchant_reply      TEXT,                -- 商家回复原文
                reply_translation   TEXT,                -- 商家回复翻译
                child_rating        TEXT,                -- 子评分（JSON对象）
                page_url            TEXT,                -- 页面URL
                -- 分析字段
                review_type         TEXT NOT NULL DEFAULT '评论',
                sentiment           TEXT,
                sentiment_score     REAL,
                keywords            TEXT,
                suggested_reply     TEXT,
                is_replied          INTEGER DEFAULT 0,
                -- 元数据
                ocr_strategy        TEXT,
                raw_data            TEXT
            );

            CREATE TABLE IF NOT EXISTS crawl_tasks (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                platform      TEXT NOT NULL,
                shop_id       TEXT NOT NULL,
                shop_name     TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'pending',
                started_at    TEXT,
                finished_at   TEXT,
                total_fetched INTEGER DEFAULT 0,
                error_msg     TEXT,
                ocr_strategy  TEXT DEFAULT 'hybrid'
            );

            CREATE INDEX IF NOT EXISTS idx_reviews_platform   ON reviews(platform);
            CREATE INDEX IF NOT EXISTS idx_reviews_shop_id    ON reviews(shop_id);
            CREATE INDEX IF NOT EXISTS idx_reviews_sentiment  ON reviews(sentiment);
            CREATE INDEX IF NOT EXISTS idx_reviews_published  ON reviews(published_at);
        """)
    # 迁移旧数据库：追加新列（若不存在）
    _migrate_add_columns()


def _migrate_add_columns() -> None:
    """向旧版表追加新字段（幂等）"""
    new_cols = [
        ("translated_content", "TEXT"),
        ("published_at",        "TEXT"),
        ("image_urls",          "TEXT"),
        ("merchant_reply",      "TEXT"),
        ("reply_translation",   "TEXT"),
        ("child_rating",        "TEXT"),
        ("page_url",            "TEXT"),
        ("ocr_strategy",        "TEXT"),
    ]
    with _get_conn() as conn:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(reviews)").fetchall()}
        for col_name, col_type in new_cols:
            if col_name not in existing:
                conn.execute(f"ALTER TABLE reviews ADD COLUMN {col_name} {col_type}")

        # crawl_tasks 新字段
        task_cols = {row[1] for row in conn.execute("PRAGMA table_info(crawl_tasks)").fetchall()}
        if "ocr_strategy" not in task_cols:
            conn.execute("ALTER TABLE crawl_tasks ADD COLUMN ocr_strategy TEXT DEFAULT 'hybrid'")


# ──────────────────────── Review Repository ────────────────────────

def insert_review(review: Review) -> int:
    """插入一条评论，返回新 id"""
    sql = """
        INSERT INTO reviews
            (platform, shop_name, shop_id, reviewer_name, content, rating,
             translated_content, published_at, crawled_at,
             image_urls, merchant_reply, reply_translation, child_rating, page_url,
             review_type, sentiment, sentiment_score,
             keywords, suggested_reply, is_replied, ocr_strategy, raw_data)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    now = datetime.now().isoformat()
    params = (
        review.platform.value,
        review.shop_name,
        review.shop_id,
        review.reviewer_name,
        review.content,
        review.rating,
        review.translated_content,
        review.published_at.isoformat() if review.published_at else None,
        review.crawled_at.isoformat() if review.crawled_at else now,
        json.dumps(list(review.image_urls), ensure_ascii=False),
        review.merchant_reply,
        review.reply_translation,
        review.child_rating,
        review.page_url,
        review.review_type.value,
        review.sentiment.value if review.sentiment else None,
        review.sentiment_score,
        json.dumps(list(review.keywords), ensure_ascii=False),
        review.suggested_reply,
        int(review.is_replied),
        review.ocr_strategy,
        review.raw_data,
    )
    with _get_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def update_review_analysis(review_id: int, review: Review) -> None:
    """更新情感分析 / 关键词 / 建议回复 / 翻译"""
    sql = """
        UPDATE reviews SET
            sentiment          = ?,
            sentiment_score    = ?,
            keywords           = ?,
            suggested_reply    = ?,
            translated_content = ?,
            reply_translation  = ?
        WHERE id = ?
    """
    with _get_conn() as conn:
        conn.execute(sql, (
            review.sentiment.value if review.sentiment else None,
            review.sentiment_score,
            json.dumps(list(review.keywords), ensure_ascii=False),
            review.suggested_reply,
            review.translated_content,
            review.reply_translation,
            review_id,
        ))


def get_reviews(
    platform: Optional[Platform] = None,
    shop_id: Optional[str] = None,
    sentiment: Optional[SentimentLabel] = None,
    review_type: Optional[ReviewType] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Review]:
    """查询评论列表"""
    conditions: list[str] = []
    params: list = []
    if platform:
        conditions.append("platform = ?")
        params.append(platform.value)
    if shop_id:
        conditions.append("shop_id = ?")
        params.append(shop_id)
    if sentiment:
        conditions.append("sentiment = ?")
        params.append(sentiment.value)
    if review_type:
        conditions.append("review_type = ?")
        params.append(review_type.value)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM reviews {where} ORDER BY published_at DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_review(r) for r in rows]


def count_reviews(
    platform: Optional[Platform] = None,
    sentiment: Optional[SentimentLabel] = None,
) -> int:
    conditions: list[str] = []
    params: list = []
    if platform:
        conditions.append("platform = ?")
        params.append(platform.value)
    if sentiment:
        conditions.append("sentiment = ?")
        params.append(sentiment.value)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    with _get_conn() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM reviews {where}", params).fetchone()[0]


def get_sentiment_stats() -> list[dict]:
    sql = """
        SELECT platform,
               SUM(CASE WHEN sentiment='正面' THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN sentiment='负面' THEN 1 ELSE 0 END) as negative,
               SUM(CASE WHEN sentiment='中性' THEN 1 ELSE 0 END) as neutral,
               COUNT(*) as total,
               AVG(rating) as avg_rating
        FROM reviews
        GROUP BY platform
    """
    with _get_conn() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def get_top_keywords(
    limit: int = 20,
    platform: Optional[Platform] = None,
) -> list[tuple[str, int]]:
    """获取高频关键词，支持按平台筛选"""
    with _get_conn() as conn:
        if platform:
            rows = conn.execute(
                "SELECT keywords FROM reviews WHERE keywords IS NOT NULL AND platform = ?",
                (platform.value,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT keywords FROM reviews WHERE keywords IS NOT NULL"
            ).fetchall()
    freq: dict[str, int] = {}
    for row in rows:
        try:
            tags = json.loads(row[0])
            for tag in tags:
                if tag and len(tag) > 1:
                    freq[tag] = freq.get(tag, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]


def get_sentiment_stats_by_platform(
    platform: Optional[Platform] = None,
) -> list[dict]:
    """获取情感统计，支持按平台筛选（筛选后只返回该平台一条）"""
    where = "WHERE platform = ?" if platform else ""
    params = (platform.value,) if platform else ()
    sql = f"""
        SELECT platform,
               SUM(CASE WHEN sentiment='正面' THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN sentiment='负面' THEN 1 ELSE 0 END) as negative,
               SUM(CASE WHEN sentiment='中性' THEN 1 ELSE 0 END) as neutral,
               COUNT(*) as total,
               AVG(rating) as avg_rating
        FROM reviews
        {where}
        GROUP BY platform
    """
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_trend_data(
    platform: Optional[Platform] = None,
    days: int = 7,
) -> list[dict]:
    """获取近 N 天趋势（可按平台筛选），返回每天各情感计数"""
    where = "AND platform = ?" if platform else ""
    params: list = []
    if platform:
        params.append(platform.value)
    sql = f"""
        SELECT
            DATE(COALESCE(published_at, crawled_at)) as day,
            SUM(CASE WHEN sentiment='正面' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN sentiment='负面' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN sentiment='中性' THEN 1 ELSE 0 END) as neutral
        FROM reviews
        WHERE COALESCE(published_at, crawled_at) >= DATE('now', '-{days} days')
        {where}
        GROUP BY day
        ORDER BY day
    """
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────── CrawlTask Repository ────────────────────────

def insert_task(task: CrawlTask) -> int:
    sql = """
        INSERT INTO crawl_tasks (platform, shop_id, shop_name, status, started_at, ocr_strategy)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with _get_conn() as conn:
        cur = conn.execute(sql, (
            task.platform.value, task.shop_id, task.shop_name,
            task.status, datetime.now().isoformat(), task.ocr_strategy,
        ))
        return cur.lastrowid


def update_task_status(
    task_id: int,
    status: str,
    total_fetched: int = 0,
    error_msg: Optional[str] = None,
) -> None:
    finished = datetime.now().isoformat() if status in ("done", "failed") else None
    with _get_conn() as conn:
        conn.execute(
            "UPDATE crawl_tasks SET status=?, finished_at=?, total_fetched=?, error_msg=? WHERE id=?",
            (status, finished, total_fetched, error_msg, task_id),
        )


def get_tasks(limit: int = 50) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM crawl_tasks ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────── 工具函数 ────────────────────────

def _row_to_review(row: sqlite3.Row) -> Review:
    def _parse_json_list(raw) -> tuple:
        try:
            return tuple(json.loads(raw)) if raw else ()
        except (json.JSONDecodeError, TypeError):
            return ()

    return Review(
        id=row["id"],
        platform=Platform(row["platform"]),
        shop_name=row["shop_name"],
        shop_id=row["shop_id"],
        reviewer_name=row["reviewer_name"] or "",
        content=row["content"],
        rating=row["rating"] or 0.0,
        translated_content=row["translated_content"],
        published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
        crawled_at=datetime.fromisoformat(row["crawled_at"]) if row["crawled_at"] else datetime.now(),
        image_urls=_parse_json_list(row["image_urls"]),
        merchant_reply=row["merchant_reply"],
        reply_translation=row["reply_translation"],
        child_rating=row["child_rating"],
        page_url=row["page_url"],
        review_type=ReviewType(row["review_type"]) if row["review_type"] else ReviewType.REVIEW,
        sentiment=SentimentLabel(row["sentiment"]) if row["sentiment"] else None,
        sentiment_score=row["sentiment_score"],
        keywords=_parse_json_list(row["keywords"]),
        suggested_reply=row["suggested_reply"],
        is_replied=bool(row["is_replied"]),
        ocr_strategy=row["ocr_strategy"],
        raw_data=row["raw_data"],
    )
