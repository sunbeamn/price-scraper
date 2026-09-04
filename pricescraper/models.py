"""Tüm site adaptörlerinin döndürdüğü ortak veri tipi."""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    site: str
    name: str
    price: Optional[float]          # TL cinsinden, sayısal
    url: str
    currency: str = "TRY"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def short_name(self) -> str:
        """Terminal tablosunda satır taşmasın diye kısaltılmış ad."""
        n = " ".join(self.name.split())
        return n if len(n) <= 60 else n[:57] + "..."
