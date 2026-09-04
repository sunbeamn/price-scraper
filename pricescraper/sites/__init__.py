"""Site adaptörü kaydı.

Yeni site eklemek = buraya bir satır.
"""

from .amazon_tr import AmazonTR
from .books_demo import BooksDemo
from .hepsiburada import Hepsiburada
from .mediamarkt import MediaMarkt
from .n11 import N11
from .trendyol import Trendyol

REGISTRY = {
    cls.name: cls
    for cls in (N11, AmazonTR, MediaMarkt, Hepsiburada, Trendyol, BooksDemo)
}

#: Argüman verilmezse kullanılan siteler (hepsi düz requests ile çalışır,
#: yani tarayıcı kurulumu gerektirmez).
DEFAULT_SITES = ["n11", "amazon", "mediamarkt"]


def get_adapter(name: str):
    try:
        return REGISTRY[name]()
    except KeyError:
        raise SystemExit(
            f"Bilinmeyen site: {name}\nGeçerli olanlar: {', '.join(REGISTRY)}"
        )
