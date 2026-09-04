"""n11.com - klasik HTML kazıma örneği.

Sunucu tarafında render ediliyor, düz requests ile alınabiliyor.
Kart yapısı:  a.product-item
                 .product-item-image div[title]   -> ürün adı
                 .basket-price h3.price-currency  -> indirimli (sepet) fiyatı
                 .basket-price div.price          -> normal/üstü çizili fiyat
"""

from urllib.parse import quote_plus

from ..models import Product
from ..parsing import parse_price, parse_int
from .base import SiteAdapter


class N11(SiteAdapter):
    name = "n11"
    base_url = "https://www.n11.com"

    def search_url(self, query: str, page: int = 1) -> str:
        url = f"{self.base_url}/arama?q={quote_plus(query)}"
        return url if page == 1 else f"{url}&pg={page}"

    def parse(self, html: str) -> list[Product]:
        soup = self.soup(html)
        products = []

        for card in soup.select("a.product-item"):
            title_el = card.select_one(".product-item-image div[title]")
            img = card.select_one("img[alt]")
            name = (title_el.get("title") if title_el
                    else img.get("alt") if img else None)
            if not name:
                continue

            # Sepet fiyatı varsa o geçerli, yoksa liste fiyatı
            final = card.select_one(".basket-price h3.price-currency")
            listed = card.select_one(".basket-price div.price")
            price = parse_price(final.get_text() if final else
                                listed.get_text() if listed else None)

            rating_el = card.select_one(".rate-number-text")

            products.append(Product(
                site=self.name,
                name=name.strip(),
                price=price,
                url=self.absolute(card.get("href", "")),
                review_count=parse_int(rating_el.get_text()) if rating_el else None,
            ))

        return products
