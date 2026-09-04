# Fiyat Kazıyıcı (Türk e-ticaret siteleri)

Terminalden çalışan, birden fazla e-ticaret sitesinde aynı ürünü arayıp
fiyatları tek tabloda karşılaştıran bir Python aracı. Arayüz yok, Django yok —
ödevde asıl mesele veriyi **toplayabilmek**, ki bu sitelerin çoğu tam olarak
bunu engellemeye çalışıyor.

```
$ python scrape.py "macbook air m2" --limit 3 --contains macbook

[n11] aranıyor: 'macbook air m2'
    sayfa 1: 20 ürün
[amazon] aranıyor: 'macbook air m2'
    sayfa 1: 48 ürün
[mediamarkt] aranıyor: 'macbook air m2'
    sayfa 1: 5 ürün

------------------------------------------------------------------------------
SITE        ÜRÜN                                                         FİYAT
------------------------------------------------------------------------------
n11         Apple MacBook Air MDHH4TU/A M5 16 GB 512 GB SSD 13.6"  74.259,06 TL
amazon      Apple M5 çipli 13 inç MacBook Air Laptop: 13.6 inç ...  82.999,00 TL
mediamarkt  APPLE MDVQ4TU/A/MacBook Air/Apple M5 İşlemci(10 Çek...  94.999,00 TL
------------------------------------------------------------------------------

Site bazında en düşük fiyat:
  amazon         82.999,00 TL   (3 ürün)  Apple M5 çipli 13 inç MacBook Air...
  mediamarkt     94.999,00 TL   (3 ürün)  APPLE MDVQ4TU/A/MacBook Air/Appl...
  n11            74.259,06 TL   (3 ürün)  Apple MacBook Air MDHH4TU/A M5 1...

EN UCUZ -> 74.259,06 TL  [n11]
```

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`selenium` yalnızca bot korumalı siteler (Hepsiburada, Trendyol) için gerekli;
kurulu değilse diğer siteler normal çalışır. Selenium için ayrıca Google Chrome
kurulu olmalı (sürücüyü Selenium 4 kendisi indiriyor, ayrı chromedriver
gerekmiyor).

## Kullanım

```bash
# En basit hali - varsayılan 3 site (n11, Amazon TR, MediaMarkt)
python scrape.py "macbook air m2"

# Belirli siteler, site başına 5 ürün, fiyata göre sıralı
python scrape.py "airfryer" --sites n11 amazon --limit 5 --sort price

# Bot korumalı siteler - tarayıcı motoru otomatik devreye girer
python scrape.py "iphone 15" --sites hepsiburada trendyol

# Aksesuar/kılıf ayıkla, fiyat aralığı ver
python scrape.py "macbook air m2" --contains macbook --min-price 30000

# Çıktıyı dosyaya al
python scrape.py "logitech mx master" --csv sonuc.csv --json sonuc.json

# Fiyat geçmişi: her çalıştırmayı veritabanına yaz, sonra trendi gör
python scrape.py "macbook air m2" --save
python scrape.py --history "macbook air m2"

# Kodun mu bozuk, site mi engelliyor? Her zaman çalışan demo site:
python scrape.py "the" --sites demo
```

Tüm seçenekler: `python scrape.py --help`

## Desteklenen siteler

| Site | Kod | Yöntem | Not |
|---|---|---|---|
| n11.com | `n11` | requests + CSS seçici | Sunucu tarafında render, sorunsuz |
| amazon.com.tr | `amazon` | requests + CSS seçici | Fiyat gizli `.a-offscreen` içinde |
| mediamarkt.com.tr | `mediamarkt` | requests + JSON-LD | Sunucudan yalnızca ilk ~5 ürün geliyor |
| hepsiburada.com | `hepsiburada` | **Selenium** | requests ile HTTP 403 |
| trendyol.com | `trendyol` | **Selenium** | requests ile HTTP 403 |
| books.toscrape.com | `demo` | requests | Kazıma pratiği için yapılmış test sitesi |

`hepsiburada` ve `trendyol` adaptörleri `needs_browser = True` işaretli, yani
`--engine` yazmasanız da otomatik olarak tarayıcı üzerinden çalışırlar.

## Siteler kazımayı nasıl engelliyor, biz ne yapıyoruz?

Ödevin asıl zor kısmı burası. Sırayla denenip test edilenler:

**1. Hiçbir başlık göndermemek.** Python `requests` varsayılan olarak
`User-Agent: python-requests/2.32.3` gönderir. Bu, "ben bir botum" demenin en
kısa yolu. Sonuç: anında 403.

**2. Tarayıcı başlıkları eklemek.** Gerçek bir Chrome'un gönderdiği
`User-Agent`, `Accept-Language: tr-TR`, `Sec-Fetch-*` başlıklarını taklit
ediyoruz (`pricescraper/http.py`). **n11, Amazon TR ve MediaMarkt bu adımda
açıldı.** Hepsiburada ve Trendyol açılmadı — onlar TLS parmak izi ve JavaScript
challenge kullanıyor, ki bunlar başlık taklidiyle geçilemez.

**3. Session + hız sınırı.** Tek bir `requests.Session` ile çerezleri
koruyoruz ve istekler arası en az 1.5 saniye (`--delay`) bekliyoruz. Bu hem
engellenmemek için hem de nezaket: saniyede yüzlerce istek atmak siteye zarar
verir.

**4. Yeniden deneme.** 429 (çok fazla istek) ve 5xx hatalarında artan bekleme
ile 3 kez deniyoruz, her denemede User-Agent'ı değiştiriyoruz.

**5. Proxy desteği.** IP'niz engellendiyse `--proxy http://host:port` veya
`HTTPS_PROXY` ortam değişkeni. (Ödev için gerekmedi, altyapı hazır.)

**6. Gerçek tarayıcı (Selenium).** Adım 2'nin yetmediği yerde tek çözüm:
gerçekten Chrome açıp sayfayı JavaScript'iyle birlikte çalıştırmak
(`pricescraper/http.render`). `navigator.webdriver` bayrağını da gizliyoruz.
Hepsiburada ve Trendyol bu şekilde açıldı. Bedeli: istek başına ~10 saniye ve
Chrome kurulumu gerektirmesi.

## Yol boyunca çarpılan tuzaklar

Bunlar tahmin değil, bu projede gerçekten karşılaşıldı:

- **`Accept-Encoding: br` göndermeyin.** Tarayıcılar brotli sıkıştırmasını
  destekler; `requests` ancak `brotli` paketi kuruluysa destekler. Kurulu
  değilse sayfa binary çöp olarak gelir, BeautifulSoup sessizce boş liste
  döndürür ve siz "site beni engelledi" sanıp yanlış yerde ararsınız.
  MediaMarkt tam olarak bu yüzden bir süre boş döndü.
- **Türkçe fiyat formatı.** `"3.699 TL"` üç bin altı yüz doksan dokuzdur,
  3.699 değil. Binlik ayracı nokta, ondalık ayracı virgül. Ayrıca Amazon
  fiyatla "TL" arasında normal boşluk değil kırılmaz boşluk (`\xa0`), Hepsiburada
  ise fiyatı `47.999` + `,04 TL` diye iki parçaya bölüyor. Hepsi
  `pricescraper/parsing.py` içinde ele alınıyor ve `tests/` altında test edilmiş.
- **Trendyol'da ürün kartının kendisi `<a>` etiketi.** Link kartın *içinde*
  değil, kartın kendisinde. `card.select_one("a")` boş döner.
- **Trendyol'da marka/ad `data-testid` ile değil sınıf adıyla işaretli** —
  kart `data-testid` taşıdığı için insan otomatik olarak içindekilerin de
  taşıdığını varsayıyor. Taşımıyorlar.
- **Hepsiburada'nın sınıf isimleri hash'li** (`title-module_titleRoot__dNDiZ`)
  ve her derlemede değişir. Bu yüzden tam sınıf adına değil, `data-test-id`
  ve sınıf **ön ekine** bağlanıyoruz (`[class*="title-module"]`).
- **Amazon sponsorlu ürünler için `/sspa/click?...` yönlendirme linki verir.**
  Gerçek ürün adresini query string içinden çıkarmak gerekiyor.
- **403 her zaman "kalıcı olarak engellendiniz" demek değil.** n11 art arda
  çok istek atılınca geçici olarak 403 döndürüyor; birkaç dakika sonra ya da
  `--delay 3` ile normale dönüyor. Kod bu durumda artan beklemeyle yeniden
  deniyor ve pes ederse hangi sitenin engellediğini açıkça yazıyor.
- **JSON-LD varsa önce ona bakın.** Birçok site, Google için ürünleri
  `<script type="application/ld+json">` içinde hazır JSON olarak gömüyor
  (MediaMarkt böyle). CSS seçicileri site tasarımı değişince kırılır, JSON-LD
  şeması kırılmaz. Yeni bir siteye başlarken ilk kontrol:
  `grep -o 'application/ld+json' sayfa.html`

## Yeni site eklemek

`pricescraper/sites/` altına bir dosya, sonra `sites/__init__.py` içindeki
`REGISTRY`'ye bir satır. Geri kalan her şey (istek atma, hız sınırı, filtreler,
tablo, CSV, veritabanı) ortak:

```python
class YeniSite(SiteAdapter):
    name = "yenisite"
    base_url = "https://www.yenisite.com"
    needs_browser = False       # requests yetmiyorsa True

    def search_url(self, query, page=1):
        return f"{self.base_url}/ara?q={quote_plus(query)}"

    def parse(self, html):
        soup = self.soup(html)
        return [
            Product(site=self.name,
                    name=card.select_one(".ad").get_text(strip=True),
                    price=parse_price(card.select_one(".fiyat").get_text()),
                    url=self.absolute(card.get("href")))
            for card in soup.select(".urun-karti")
        ]
```

## Proje yapısı

```
scrape.py                    komut satırı arayüzü
pricescraper/
    models.py                Product veri tipi (tüm siteler bunu döndürür)
    http.py                  başlıklar, hız sınırı, yeniden deneme, Selenium
    parsing.py               Türkçe fiyat metni -> float
    output.py                terminal tablosu, CSV, JSON
    storage.py               SQLite fiyat geçmişi
    sites/
        base.py              adaptör sözleşmesi
        n11.py  amazon_tr.py  mediamarkt.py
        hepsiburada.py  trendyol.py  books_demo.py
tests/test_parsing.py        gerçek site metinleriyle fiyat ayrıştırma testleri
```

## Testler

```bash
python tests/test_parsing.py        # pytest kurulu olmasa da çalışır
```

## Sorumluluk notu

Bu araç bir ödev/öğrenme projesidir. Sadece herkese açık fiyat sayfalarını
okur, hesap açmaz, giriş yapmaz. İstekler arasında bekleme koyulmuştur
(`--delay`); bu değeri düşürmeyin. Toplanan veriyi ticari olarak kullanmadan
önce ilgili sitenin kullanım şartlarına ve `robots.txt` dosyasına bakın.
Siteler tasarımlarını değiştirdiğinde adaptörlerin bozulması normaldir —
bu yüzden her adaptör bağımsız ve tek dosyadır.
