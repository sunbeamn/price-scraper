#!/usr/bin/env python3
"""Türk e-ticaret sitelerinden fiyat toplayan terminal aracı.

Örnekler
--------
    python scrape.py "macbook air m2"
    python scrape.py "airfryer" --sites n11 amazon --limit 5 --sort price
    python scrape.py "iphone 15" --sites hepsiburada trendyol --engine selenium
    python scrape.py "logitech mx master" --csv sonuc.csv --save
    python scrape.py --history "macbook air m2"
"""

import argparse
import sys

from pricescraper import output, storage
from pricescraper.http import BlockedError, Fetcher, render
from pricescraper.models import Product
from pricescraper.sites import DEFAULT_SITES, REGISTRY, get_adapter


def collect(query: str, site_names: list[str], args) -> list[Product]:
    fetcher = Fetcher(delay=args.delay, proxy=args.proxy, verbose=args.verbose)
    results: list[Product] = []

    for name in site_names:
        adapter = get_adapter(name)
        # Site zaten tarayıcı istiyorsa kullanıcı --engine yazmasa da geç
        use_browser = args.engine == "selenium" or adapter.needs_browser

        print(f"\n[{adapter.name}] aranıyor: {query!r}"
              f"{'  (tarayıcı motoru)' if use_browser else ''}")

        found: list[Product] = []
        for page in range(1, args.pages + 1):
            url = adapter.search_url(query, page)
            try:
                html = render(url, wait=args.wait) if use_browser else fetcher.get(url)
            except BlockedError as e:
                output.warn(f"{adapter.name} engelledi ({e}). "
                            f"'--engine selenium' ile tarayıcı üzerinden deneyin.")
                break
            except Exception as e:                      # ağ, tarayıcı, timeout...
                output.warn(f"{adapter.name} alınamadı: {type(e).__name__}: {e}")
                break

            try:
                page_products = adapter.parse(html)
            except Exception as e:
                output.warn(f"{adapter.name} ayrıştırılamadı: {type(e).__name__}: {e}"
                            f"  (site tasarımını değiştirmiş olabilir)")
                break

            if not page_products:
                output.warn(f"{adapter.name} sayfa {page}: sonuç yok, duruldu.")
                break

            found.extend(page_products)
            print(f"    sayfa {page}: {len(page_products)} ürün")

        # Demo sitesinde arama olmadığı için sorguyu burada filtre olarak uygula
        if adapter.name == "demo" and query:
            found = [p for p in found if query.lower() in p.name.lower()]

        results.extend(found[:args.limit] if args.limit else found)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="E-ticaret sitelerinden fiyat toplar ve karşılaştırır.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("query", nargs="?", help="Aranacak ürün, ör: 'macbook air m2'")
    parser.add_argument("--sites", nargs="+", default=DEFAULT_SITES,
                        metavar="SITE",
                        help=f"Taranacak siteler. Seçenekler: {', '.join(REGISTRY)}. "
                             f"Varsayılan: {' '.join(DEFAULT_SITES)}")
    parser.add_argument("--pages", type=int, default=1,
                        help="Site başına kaç arama sayfası (varsayılan 1)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Site başına en fazla kaç ürün (0 = sınırsız)")
    parser.add_argument("--sort", choices=["price", "site", "none"], default="price",
                        help="Sonuç sıralaması (varsayılan: price)")
    parser.add_argument("--max-price", type=float, metavar="TL",
                        help="Bu fiyatın üstündeki ürünleri ele")
    parser.add_argument("--min-price", type=float, metavar="TL",
                        help="Bu fiyatın altındaki ürünleri ele")
    parser.add_argument("--contains", metavar="KELIME",
                        help="Ürün adında bu kelime geçmeyenleri ele "
                             "(aksesuar/kılıf ayıklamak için)")

    parser.add_argument("--engine", choices=["requests", "selenium"], default="requests",
                        help="requests: hızlı, JS çalıştırmaz. "
                             "selenium: gerçek Chrome açar, korumalı siteleri geçer.")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="İstekler arası bekleme, saniye (varsayılan 1.5)")
    parser.add_argument("--wait", type=float, default=4.0,
                        help="Selenium'da sayfa yüklenme beklemesi (varsayılan 4)")
    parser.add_argument("--proxy", help="Proxy adresi, ör: http://kullanici:sifre@host:port")

    parser.add_argument("--csv", metavar="DOSYA", help="Sonuçları CSV'ye yaz")
    parser.add_argument("--json", metavar="DOSYA", help="Sonuçları JSON'a yaz")
    parser.add_argument("--save", action="store_true",
                        help="Sonuçları prices.db'ye ekle (fiyat geçmişi için)")
    parser.add_argument("--db", default="prices.db", help="Veritabanı dosyası")
    parser.add_argument("--history", metavar="SORGU",
                        help="Kazıma yapmadan, kayıtlı fiyat geçmişini göster")
    parser.add_argument("--urls", action="store_true", help="Tabloda linkleri de göster")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Atılan her isteği yazdır")

    args = parser.parse_args()

    if args.history:
        storage.history(args.history, args.db)
        return 0

    if not args.query:
        parser.error("bir arama sorgusu verin, ör: python scrape.py \"macbook air m2\"")

    products = collect(args.query, args.sites, args)

    # --- filtreler ---
    if args.contains:
        needle = args.contains.lower()
        products = [p for p in products if needle in p.name.lower()]
    if args.min_price is not None:
        products = [p for p in products
                    if p.price is not None and p.price >= args.min_price]
    if args.max_price is not None:
        products = [p for p in products
                    if p.price is not None and p.price <= args.max_price]

    # --- sıralama: fiyatı olmayanlar hep sona ---
    if args.sort == "price":
        products.sort(key=lambda p: (p.price is None, p.price or 0))
    elif args.sort == "site":
        products.sort(key=lambda p: (p.site, p.price is None, p.price or 0))

    print()
    output.print_table(products, show_url=args.urls)
    output.print_summary(products)

    if args.csv:
        output.write_csv(products, args.csv)
    if args.json:
        output.write_json(products, args.json)
    if args.save:
        storage.save(products, args.query, args.db)

    return 0 if products else 1


if __name__ == "__main__":
    sys.exit(main())
