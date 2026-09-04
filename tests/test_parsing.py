"""Fiyat ayrıştırıcı testleri.

Çalıştırmak için:  python -m pytest tests/    (veya: python tests/test_parsing.py)

Kazıyıcının en sinsi hata kaynağı bu: "3.699 TL" 3699 mü 3.699 mu?
Türkçe formatta binlik ayracı nokta olduğu için 3699'dur. Bu testler
kazıdığımız sitelerden ALINAN gerçek metinleri içeriyor.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pricescraper.parsing import format_price, parse_int, parse_price

CASES = [
    ("46.999,06 TL", 46999.06),     # n11
    ("3.699 TL", 3699.0),           # n11 - nokta binlik ayracı
    ("369,60 TL", 369.6),           # n11 - virgül ondalık
    ("110.399,00\xa0TL", 110399.0),  # Amazon - kırılmaz boşluk
    ("47.999 ,04 TL", 47999.04),    # Hepsiburada - fiyat iki parça
    ("49.999 TL", 49999.0),         # Trendyol
    (1225.44, 1225.44),             # MediaMarkt JSON-LD - zaten sayı
    ("£51.77", 51.77),              # demo sitesi - İngilizce format
    ("", None),
    (None, None),
    ("Fiyat sorunuz", None),
]


def test_parse_price():
    for raw, expected in CASES:
        got = parse_price(raw)
        assert got == expected, f"{raw!r} -> {got}, beklenen {expected}"


def test_format_price():
    assert format_price(46999.06) == "46.999,06 TL"
    assert format_price(None) == "-"
    assert format_price(51.77, "GBP") == "51,77 GBP"


def test_round_trip():
    """Biçimlendirilmiş fiyat geri okunduğunda aynı sayıyı vermeli."""
    for value in (0.5, 369.6, 46999.06, 110399.0):
        assert parse_price(format_price(value)) == value


def test_parse_int():
    assert parse_int("(134)") == 134
    assert parse_int("1.234 değerlendirme") == 1234
    assert parse_int("yorum yok") is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"  ok  {name}")
    print("Tüm testler geçti.")
