"""Site adaptörü sözleşmesi.

Yeni bir site eklemek için: bu sınıftan türet, `name` ve `search_url` ver,
`parse` yaz, sonra sites/__init__.py içindeki REGISTRY'ye ekle.
Geri kalan her şey (istek atma, hız sınırı, çıktı, CSV) ortak.
"""

from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from ..models import Product


class SiteAdapter(ABC):
    name: str = "site"
    base_url: str = ""
    #: Bu site düz requests ile alınamıyorsa True (Selenium gerekir)
    needs_browser: bool = False

    @abstractmethod
    def search_url(self, query: str, page: int = 1) -> str:
        """Arama sorgusu için tam URL üretir."""

    @abstractmethod
    def parse(self, html: str) -> list[Product]:
        """Arama sonuç sayfasının HTML'inden ürün listesi çıkarır."""

    # --- yardımcılar -----------------------------------------------------
    def soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def absolute(self, href: str) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        return self.base_url.rstrip("/") + "/" + href.lstrip("/")
