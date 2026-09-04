"""HTTP katmanı: tarayıcı gibi görünen başlıklar, yeniden deneme, hız sınırı.

Ödevin asıl zorluğu burada: siteler otomatik istekleri engelliyor.
Uyguladığımız önlemler:
  1. Gerçekçi User-Agent + Accept-Language (tr-TR) başlıkları
  2. Session ile çerezleri koruma (ilk istek çerez alır, sonrakiler kullanır)
  3. İstekler arası bekleme (rate limit) - hem engellenmemek hem nezaket
  4. 429/5xx için artan bekleme ile yeniden deneme
  5. İsteğe bağlı proxy desteği (HTTPS_PROXY ortam değişkeni veya --proxy)
"""

import os
import random
import time

import requests

# Farklı istekler için birkaç gerçek tarayıcı imzası; hep aynısını
# göndermek tek başına bir parmak izidir.
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
              "image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    # DİKKAT: "br" (brotli) YAZMAYIN. Tarayıcılar gönderir ama requests
    # brotli'yi ancak `brotli` paketi kuruluysa çözebilir; kurulu değilse
    # sayfa binary çöp olarak gelir ve BeautifulSoup sessizce boş liste
    # döndürür - "site engelledi" sanıp saatlerce yanlış yerde aranır.
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


class BlockedError(RuntimeError):
    """Site isteği reddetti (403/429/captcha)."""


class Fetcher:
    def __init__(self, delay: float = 1.5, timeout: int = 25,
                 retries: int = 3, proxy: str | None = None,
                 verbose: bool = False):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.verbose = verbose
        self._last_request = 0.0

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers["User-Agent"] = random.choice(USER_AGENTS)

        proxy = proxy or os.environ.get("HTTPS_PROXY")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def _wait(self):
        """Ardışık istekler arasında en az `delay` saniye bırak."""
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed + random.uniform(0, 0.4))
        self._last_request = time.time()

    def get(self, url: str, referer: str | None = None) -> str:
        headers = {"Referer": referer} if referer else {}
        last_error = None

        for attempt in range(1, self.retries + 1):
            self._wait()
            if self.verbose:
                print(f"    GET {url}  (deneme {attempt}/{self.retries})")
            try:
                r = self.session.get(url, headers=headers, timeout=self.timeout)
            except requests.RequestException as e:
                last_error = e
                time.sleep(2 ** attempt)
                continue

            if r.status_code in (403, 429):
                last_error = BlockedError(f"HTTP {r.status_code} - engellendi")
                # 429 geçici olabilir, artan bekleme ile tekrar dene
                time.sleep(2 ** attempt + random.uniform(0, 1))
                self.session.headers["User-Agent"] = random.choice(USER_AGENTS)
                continue

            if r.status_code >= 500:
                last_error = RuntimeError(f"HTTP {r.status_code}")
                time.sleep(2 ** attempt)
                continue

            r.raise_for_status()
            return r.text

        raise last_error if last_error else RuntimeError("bilinmeyen hata")


def render(url: str, wait: float = 4.0, headless: bool = True) -> str:
    """Selenium ile sayfayı gerçek tarayıcıda açıp HTML'i döndürür.

    JS ile yüklenen listeler ve bazı bot korumaları için. selenium +
    Chrome kurulu değilse anlaşılır bir hata verir.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as e:
        raise RuntimeError(
            "selenium kurulu değil. Kurmak için: pip install selenium"
        ) from e

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    opts.add_argument("--lang=tr-TR")
    # "Beni otomasyon çalıştırıyor" bayrağını kaldır
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=opts)
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
        )
        driver.get(url)
        time.sleep(wait)                       # JS'in listeyi doldurmasını bekle
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
        time.sleep(1.5)                        # lazy-load ürünler için
        return driver.page_source
    finally:
        driver.quit()
