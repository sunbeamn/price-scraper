"""amazon.com.tr - kart tabanlı kazıma.

Amazon kartları data-component-type="s-search-result" ile işaretli.
Fiyat, ekran okuyucular için gizli bir <span class="a-offscreen"> içinde
tam metin olarak duruyor - görünen fiyat parça parça yazıldığı için
kazımanın doğru yeri burası.

Not: Amazon sponsorlu ("/sspa/click?...") linkler döndürüyor; onları
gerçek ürün sayfasına çeviriyoruz.
"""

from urllib.parse import quote_plus, urlparse, parse_qs, unquote

from ..models import Product
from ..parsing import parse_price, parse_int
from .base import SiteAdapter


class AmazonTR(SiteAdapter):
    name = "amazon"
    base_url = "https://www.amazon.com.tr"

    def search_url(self, query: str, page: int = 1) -> str:
        url = f"{self.base_url}/s?k={quote_plus(query)}"
        return url if page == 1 else f"{url}&page={page}"

    def _clean_url(self, href: str, asin: str | None) -> str:
        """Sponsorlu tıklama linkini sadeleştir."""
        if "/sspa/click" in href:
            qs = parse_qs(urlparse(href).query)
            if "url" in qs:
                return self.absolute(unquote(qs["url"][0]))
            if asin:
                return f"{self.base_url}/dp/{asin}"
        return self.absolute(href)

    def parse(self, html: str) -> list[Product]:
        soup = self.soup(html)
        products = []

        for card in soup.select('div[data-component-type="s-search-result"]'):
            title = card.select_one("h2")
            if not title:
                continue

            price_el = card.select_one(".a-price .a-offscreen")
            link = card.select_one("a.a-link-normal[href]")
            asin = card.get("data-asin") or None

            rating = card.select_one("span.a-icon-alt")          # "4,5 üzerinden 5 yıldız"
            reviews = card.select_one('span[aria-label][class*="s-underline"]') \
                or card.select_one("span.a-size-base.s-underline-text")

            products.append(Product(
                site=self.name,
                name=title.get_text(" ", strip=True),
                price=parse_price(price_el.get_text() if price_el else None),
                url=self._clean_url(link.get("href", "") if link else "", asin),
                rating=parse_price(rating.get_text().split()[0]) if rating else None,
                review_count=parse_int(reviews.get_text()) if reviews else None,
            ))

        return products
