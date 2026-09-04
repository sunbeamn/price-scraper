"""mediamarkt.com.tr - JSON-LD (yapısal veri) kazıma örneği.

Birçok site, Google'ın zengin sonuçlarda gösterebilmesi için ürünleri
sayfaya <script type="application/ld+json"> içinde HAZIR JSON olarak
gömüyor. Bu, HTML sınıf isimlerini kovalamaktan çok daha sağlam bir
yöntemdir: site tasarımını değiştirdiğinde CSS seçicileri kırılır ama
JSON-LD şeması (schema.org) sabit kalır.

Yeni bir siteye başlarken önce buna bakın:
    grep -o 'application/ld+json' sayfa.html

Kısıt: MediaMarkt sunucudan yalnızca ilk ~5 ürünü render ediyor,
gerisini kaydırdıkça JS yüklüyor. Daha fazlası için --engine selenium.
"""

import json
from urllib.parse import quote_plus

from ..models import Product
from ..parsing import parse_price
from .base import SiteAdapter


class MediaMarkt(SiteAdapter):
    name = "mediamarkt"
    base_url = "https://www.mediamarkt.com.tr"

    def search_url(self, query: str, page: int = 1) -> str:
        url = f"{self.base_url}/tr/search.html?query={quote_plus(query)}"
        return url if page == 1 else f"{url}&page={page}"

    def parse(self, html: str) -> list[Product]:
        soup = self.soup(html)
        products = []

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue

            if data.get("@type") != "ItemList":
                continue

            for entry in data.get("itemListElement", []):
                item = entry.get("item", {})
                if item.get("@type") != "Product":
                    continue

                offer = item.get("offers") or {}
                rating = item.get("aggregateRating") or {}

                products.append(Product(
                    site=self.name,
                    name=item.get("name", "").strip(),
                    price=parse_price(offer.get("price")),
                    url=self.absolute(item.get("url", "")),
                    currency=offer.get("priceCurrency", "TRY"),
                    rating=rating.get("ratingValue"),
                    review_count=rating.get("reviewCount"),
                ))

        return products
