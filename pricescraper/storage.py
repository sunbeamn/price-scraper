"""Fiyat geçmişi: her çalıştırmayı SQLite'a yazar.

Tek seferlik kazıma "şu an kaç lira" sorusunu yanıtlar. Aynı sorguyu
günlerce çalıştırıp veritabanına yazarsanız "ucuzladı mı?" sorusunu da
yanıtlayabilirsiniz - fiyat takip uygulamalarının yaptığı tam olarak bu.
"""

import sqlite3
from contextlib import closing

from .models import Product

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    query       TEXT    NOT NULL,
    site        TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    price       REAL,
    currency    TEXT,
    url         TEXT,
    scraped_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_prices_query ON prices(query, scraped_at);
CREATE INDEX IF NOT EXISTS idx_prices_url   ON prices(url, scraped_at);
"""


def connect(path: str = "prices.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save(products: list[Product], query: str, path: str = "prices.db") -> int:
    with closing(connect(path)) as conn, conn:
        conn.executemany(
            "INSERT INTO prices (query, site, name, price, currency, url, scraped_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(query, p.site, p.name, p.price, p.currency, p.url, p.scraped_at)
             for p in products],
        )
    print(f"{len(products)} kayıt veritabanına yazıldı: {path}")
    return len(products)


def history(query: str, path: str = "prices.db", limit: int = 30) -> None:
    """Bir sorgu için gün gün en düşük fiyatı gösterir."""
    with closing(connect(path)) as conn:
        rows = conn.execute(
            """
            SELECT date(scraped_at) AS gun, site,
                   MIN(price) AS en_dusuk, COUNT(*) AS adet
            FROM prices
            WHERE query = ? AND price IS NOT NULL
            GROUP BY gun, site
            ORDER BY gun DESC, site
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

    if not rows:
        print(f"'{query}' için kayıt yok. Önce --save ile bir arama çalıştırın.")
        return

    from .parsing import format_price
    print(f"\n'{query}' fiyat geçmişi (günlük en düşük):")
    print(f"{'TARİH':<12} {'SITE':<12} {'EN DÜŞÜK':>14} {'ÜRÜN':>6}")
    print("-" * 48)
    for r in rows:
        print(f"{r['gun']:<12} {r['site']:<12} "
              f"{format_price(r['en_dusuk']):>14} {r['adet']:>6}")
