import gzip
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class Store:
    code: str
    type: str
    address: str
    postcode: str
    city: str


@dataclass
class FileRef:
    url: str
    filename: str
    date: date
    store: Store


@dataclass
class PriceRecord:
    product_code: str
    name: str
    brand: str | None
    net_quantity: str | None
    unit: str | None
    price: float | None
    unit_price: float | None
    is_promo: bool
    promo_name: str | None
    base_price: float | None
    lowest_30d: float | None
    barcode: str | None
    anchor_price: float | None = None


def open_text(path):
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return open(path, encoding="utf-8", newline="")


class Chain(ABC):
    name = ""

    @abstractmethod
    def available_dates(self) -> list[date]: ...

    @abstractmethod
    def discover(self, day: date) -> list[FileRef]: ...

    @abstractmethod
    def parse(self, path: Path): ...

    @abstractmethod
    def parse_store(self, filename: str) -> Store: ...
