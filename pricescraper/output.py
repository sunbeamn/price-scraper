"""Terminal tablosu, CSV ve JSON çıktıları."""

import csv
import json
import sys
from collections import Counter

from .models import Product
from .parsing import format_price

COLUMNS = ["site", "name", "price", "url", "currency", "rating",
           "review_count", "scraped_at"]


def print_table(products: list[Product], show_url: bool = False) -> None:
    if not products:
        print("Hiç ürün bulunamadı.")
        return

    rows = [(p.site, p.short_name, format_price(p.price, p.currency))
            for p in products]
    w_site = max(len("SITE"), *(len(r[0]) for r in rows))
    w_name = max(len("ÜRÜN"), *(len(r[1]) for r in rows))
    w_price = max(len("FİYAT"), *(len(r[2]) for r in rows))

    line = "-" * (w_site + w_name + w_price + 8)
    print(line)
    print(f"{'SITE':<{w_site}}  {'ÜRÜN':<{w_name}}  {'FİYAT':>{w_price}}")
    print(line)
    for (site, name, price), p in zip(rows, products):
        print(f"{site:<{w_site}}  {name:<{w_name}}  {price:>{w_price}}")
        if show_url:
            print(f"{'':<{w_site}}  {p.url}")
    print(line)


def print_summary(products: list[Product]) -> None:
    """Fiyat karşılaştırmasının asıl çıktısı: en ucuz nerede?"""
    priced = [p for p in products if p.price is not None]
    if not priced:
        return

    print(f"\n{len(products)} ürün, {len(priced)} tanesinde fiyat var.")

    # Kur çevirisi yapmıyoruz, dolayısıyla farklı para birimlerini
    # birbiriyle kıyaslamak yanlış olur. Karşılaştırmayı sonuçlarda en
    # çok geçen para birimiyle sınırlıyoruz ve elenenleri belirtiyoruz.
    currencies = Counter(p.currency for p in priced)
    main_currency, _ = currencies.most_common(1)[0]
    comparable = [p for p in priced if p.currency == main_currency]
    if len(currencies) > 1:
        skipped = len(priced) - len(comparable)
        print(f"  (farklı para biriminde {skipped} ürün karşılaştırma dışı "
              f"bırakıldı; kur çevirisi yapılmıyor)")

    by_site: dict[str, list[Product]] = {}
    for p in comparable:
        by_site.setdefault(p.site, []).append(p)

    print("\nSite bazında en düşük fiyat:")
    for site, items in sorted(by_site.items()):
        cheapest = min(items, key=lambda x: x.price)
        print(f"  {site:<12} {format_price(cheapest.price, cheapest.currency):>14}   "
              f"({len(items)} ürün)  {cheapest.short_name}")

    best = min(comparable, key=lambda x: x.price)
    print(f"\nEN UCUZ -> {format_price(best.price, best.currency)}  [{best.site}]")
    print(f"           {best.name}")
    print(f"           {best.url}")


def write_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        # utf-8-sig: Excel Türkçe karakterleri doğru göstersin diye
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for p in products:
            writer.writerow(p.as_dict())
    print(f"CSV yazıldı: {path}")


def write_json(products: list[Product], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.as_dict() for p in products], f,
                  ensure_ascii=False, indent=2)
    print(f"JSON yazıldı: {path}")


def warn(msg: str) -> None:
    print(f"  ! {msg}", file=sys.stderr)
