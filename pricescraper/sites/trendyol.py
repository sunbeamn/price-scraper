"""trendyol.com - bot korumalı, gerçek tarayıcı gerektirir.

requests ile HTTP 403 (test edildi). Selenium ile geçiliyor.

Bu sitede dikkat çeken iki nokta:
  1. Ürün kartının KENDİSİ bir <a> etiketi (a.product-card), link
     kartın içinde değil. `card.select_one("a")` boş döner - saatlerce
     "link neden yok" diye aranabilir.
  2. İki farklı fiyat düzeni var: normal ürünlerde .single-price,
     sepet indirimli ürünlerde .price-value (üstü çizili eski fiyat
     .strikethrough-price içinde). Geçerli fiyat için önce .price-value
     bakıyoruz.
"""

from urllib.parse import quote_plus

from ..models import Product
from ..parsing import parse_price, parse_int
from .base import SiteAdapter


class Trendyol(SiteAdapter):
    name = "trendyol"
    base_url = "https://www.trendyol.com"
    needs_browser = True

    def search_url(self, query: str, page: int = 1) -> str:
        url = f"{self.base_url}/sr?q={quote_plus(query)}"
        return url if page == 1 else f"{url}&pi={page}"

    def parse(self, html: str) -> list[Product]:
        soup = self.soup(html)
        products = []

        for card in soup.select('[data-testid="product-card"]'):
            # Marka/ad SINIF ile işaretli, data-testid ile DEĞİL - kartın
            # kendisi data-testid taşıdığı için ikisini karıştırmak kolay.
            brand = card.select_one(".product-brand")
            name_el = card.select_one(".product-name")
            if not name_el:
                continue

            name = " ".join(filter(None, [
                brand.get_text(" ", strip=True) if brand else None,
                name_el.get_text(" ", strip=True),
            ]))

            price_el = (card.select_one(".price-value")
                        or card.select_one(".single-price"))
            rating = card.select_one(".average-rating")
            count = card.select_one(".total-count")

            products.append(Product(
                site=self.name,
                name=name,
                price=parse_price(price_el.get_text() if price_el else None),
                url=self.absolute((card.get("href") or "").split("?")[0]),
                rating=parse_price(rating.get_text()) if rating else None,
                review_count=parse_int(count.get_text()) if count else None,
            ))

        return products
