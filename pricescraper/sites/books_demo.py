"""books.toscrape.com - kazıma pratiği için yapılmış, engellemeyen site.

Neden burada: gerçek e-ticaret siteleri bugün çalışıp yarın tasarımını
değiştirebilir ya da IP'nizi engelleyebilir. Bu adaptör her zaman
çalışır, dolayısıyla "kod mu bozuk, site mi engelliyor?" sorusunu
ayırt etmek için sağlam bir referanstır:

    python scrape.py --sites demo --query "" --limit 5

Fiyatlar sterlin; kur çevirisi yapmıyoruz, olduğu gibi raporluyoruz.
"""

from urllib.parse import quote_plus

from ..models import Product
from ..parsing import parse_price
from .base import SiteAdapter


class BooksDemo(SiteAdapter):
    name = "demo"
    base_url = "https://books.toscrape.com"

    def search_url(self, query: str, page: int = 1) -> str:
        # Bu sitede arama yok; sayfalar arasında geziyoruz.
        # `query` bir filtre olarak parse() içinde uygulanıyor.
        if page == 1:
            return f"{self.base_url}/index.html"
        return f"{self.base_url}/catalogue/page-{page}.html"

    def _product_url(self, href: str) -> str:
        """Ana sayfada linkler 'catalogue/...', alt sayfalarda '../...'
        biçiminde geliyor; ikisini de tek biçime indiriyoruz."""
        href = href.replace("../", "")
        if not href.startswith("catalogue/"):
            href = "catalogue/" + href
        return self.absolute(href)

    def parse(self, html: str) -> list[Product]:
        soup = self.soup(html)
        products = []

        for card in soup.select("article.product_pod"):
            link = card.select_one("h3 a")
            price_el = card.select_one("p.price_color")
            if not link:
                continue

            products.append(Product(
                site=self.name,
                name=link.get("title") or link.get_text(strip=True),
                price=parse_price(price_el.get_text() if price_el else None),
                url=self._product_url(link.get("href", "")),
                currency="GBP",
            ))

        return products
