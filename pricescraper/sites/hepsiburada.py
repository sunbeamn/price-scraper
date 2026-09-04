"""hepsiburada.com - bot korumalı site, gerçek tarayıcı gerektirir.

Düz requests ile HTTP 403 dönüyor (test edildi): sunucu, TLS parmak izi
ve JS challenge ile otomatik istemcileri ayırt ediyor. Sadece User-Agent
başlığı eklemek YETMİYOR.

Çözüm: Selenium ile gerçek Chrome açıp sayfayı JS'iyle birlikte
render etmek (bkz. pricescraper/http.render). Bu yüzden
needs_browser = True; araç bu adaptörü otomatik olarak tarayıcı
motoruyla çalıştırır.

Sınıf isimleri CSS-module hash'li (title-module_titleRoot__dNDiZ) ve
her derlemede DEĞİŞİR. Bu yüzden ekteki hash'e değil, sabit kalan
data-test-id ve sınıf ÖN EKLERİNE bağlanıyoruz.
"""

from urllib.parse import quote_plus

from ..models import Product
from ..parsing import parse_price, parse_int
from .base import SiteAdapter


class Hepsiburada(SiteAdapter):
    name = "hepsiburada"
    base_url = "https://www.hepsiburada.com"
    needs_browser = True

    def search_url(self, query: str, page: int = 1) -> str:
        url = f"{self.base_url}/ara?q={quote_plus(query)}"
        return url if page == 1 else f"{url}&sayfa={page}"

    def parse(self, html: str) -> list[Product]:
        soup = self.soup(html)
        products = []

        for card in soup.select('li[class*="productListContent"]'):
            title = card.select_one('h2[class*="title-module"]')
            if not title:
                continue

            price_el = card.select_one('[data-test-id^="final-price"]')
            link = card.select_one("a[href]")
            rating = card.select_one('[class*="rate-module_rating"]')
            count = card.select_one('[class*="rate-module_count"]')

            products.append(Product(
                site=self.name,
                name=title.get_text(" ", strip=True),
                price=parse_price(price_el.get_text() if price_el else None),
                url=self.absolute(link.get("href", "") if link else ""),
                rating=parse_price(rating.get_text()) if rating else None,
                review_count=parse_int(count.get_text()) if count else None,
            ))

        return products
