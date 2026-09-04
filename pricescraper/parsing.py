"""Türkçe fiyat metinlerini sayıya çeviren yardımcılar.

Türkiye'de binlik ayracı nokta, ondalık ayracı virgüldür:
    "46.999,06 TL" -> 46999.06
Ama bazı siteler "1225.44" gibi İngilizce format da yazabiliyor.
Bu yüzden hangi ayracın ondalık olduğuna metne bakarak karar veriyoruz.
"""

import re

# 1.234,56 | 1234,56 | 1.234 | 1234.56 | 1234
_PRICE_RE = re.compile(r"\d[\d.,\s ]*\d|\d")


def parse_price(text) -> float | None:
    """Serbest metinden ilk geçen fiyatı float olarak döndürür."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)

    # \xa0 (kırılmaz boşluk) Amazon'da fiyatla "TL" arasında geçiyor
    text = str(text).replace(" ", " ")
    m = _PRICE_RE.search(text)
    if not m:
        return None

    raw = m.group(0).replace(" ", "")
    has_dot, has_comma = "." in raw, "," in raw

    if has_dot and has_comma:
        # En sağdaki ayraç ondalıktır: "46.999,06" veya "46,999.06"
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif has_comma:
        # Tek virgül: "3.699" değil "369,60" gibi -> ondalık say,
        # ama "1,234" gibi binlik de olabilir. Virgülden sonra 1-2 hane
        # varsa ondalık, 3 hane varsa binlik ayracı kabul ediyoruz.
        tail = raw.rsplit(",", 1)[1]
        raw = raw.replace(",", "." if len(tail) <= 2 else "")
    elif has_dot:
        tail = raw.rsplit(".", 1)[1]
        # "3.699" -> binlik ayracı; "1225.44" -> ondalık
        if len(tail) == 3:
            raw = raw.replace(".", "")

    try:
        return float(raw)
    except ValueError:
        return None


def parse_int(text) -> int | None:
    """'(16)' -> 16 gibi yorum sayılarını çeker."""
    if text is None:
        return None
    m = re.search(r"\d+", str(text).replace(".", "").replace(",", ""))
    return int(m.group(0)) if m else None


#: ISO kodu -> ekranda gösterilecek kısaltma
CURRENCY_LABEL = {"TRY": "TL", "TL": "TL"}


def format_price(value, currency: str = "TRY") -> str:
    """46999.06 -> '46.999,06 TL' (Türkçe binlik/ondalık düzeniyle)"""
    if value is None:
        return "-"
    s = f"{value:,.2f}"                       # 46,999.06
    # nokta ve virgülü yer değiştir: 46,999.06 -> 46.999,06
    s = s.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"{s} {CURRENCY_LABEL.get(currency, currency)}"
