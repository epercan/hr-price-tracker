import csv
import re
from datetime import date
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from tracker.chains.base import Chain, FileRef, PriceRecord, Store, open_text
from tracker.clean import clean_barcode, parse_price

BASE_URL = "https://www.konzum.hr/cjenici"
USER_AGENT = "Mozilla/5.0 (hr-price-tracker)"


def parse_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.upper().endswith(".CSV") and href not in links:
            links.append(href)
    return links


def parse_dates(html):
    found = set(re.findall(r"/cjenici\?date=(\d{4}-\d{2}-\d{2})", html))
    return sorted(date.fromisoformat(d) for d in found)


def parse_store(filename):
    parts = filename.split(",")
    store_type = parts[0].split("-", 1)[1]
    m = re.match(r"^(.*?)\s+(\d{5})\s+(.+)$", parts[1].strip())
    address, postcode, city = m.groups() if m else (parts[1].strip(), "", "")
    return Store(code=parts[2].strip(), type=store_type, address=address,
                 postcode=postcode, city=city)


class KonzumChain(Chain):
    name = "konzum"

    def __init__(self, session=None):
        if session is None:
            session = requests.Session()
            session.headers["User-Agent"] = USER_AGENT
        self.session = session

    def _get_page(self, params):
        r = self.session.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        return r.text

    def available_dates(self):
        return parse_dates(self._get_page({"page": 1}))

    def discover(self, day):
        refs = {}
        page = 1
        while True:
            links = parse_links(self._get_page({"date": day.isoformat(), "page": page}))
            new = [l for l in links if l not in refs]
            if not new:
                break
            for url in new:
                filename = unquote(url.rsplit("/", 1)[-1])
                refs[url] = FileRef(url, filename, day, parse_store(filename))
            page += 1
        return list(refs.values())

    def parse_store(self, filename):
        return parse_store(filename)

    def parse(self, path):
        with open_text(path) as f:
            for row in csv.DictReader(f):
                yield self._record(row)

    def _record(self, row):
        get = lambda key: (row.get(key) or "").strip()
        price = parse_price(get("MALOPRODAJNA CIJENA"))
        if "POSEBAN OBLIK PRODAJE" in row:
            is_promo = get("POSEBAN OBLIK PRODAJE").upper() == "DA"
            base_price = parse_price(get("BAZNA CIJENA"))
        else:
            # old format (until 2026-11-16): promo price in a separate column
            promo_price = parse_price(get("MPC ZA VRIJEME POSEBNOG OBLIKA PRODAJE"))
            is_promo = promo_price is not None
            base_price = price
            if is_promo:
                price = promo_price
        return PriceRecord(
            product_code=get("ŠIFRA PROIZVODA"),
            name=get("NAZIV PROIZVODA"),
            brand=get("MARKA PROIZVODA") or None,
            net_quantity=get("NETO KOLIČINA") or None,
            unit=get("JEDINICA MJERE") or None,
            price=price,
            unit_price=parse_price(get("CIJENA ZA JEDINICU MJERE")),
            is_promo=is_promo,
            promo_name=get("NAZIV POSEBNOG OBLIKA PRODAJE") or None,
            base_price=base_price,
            lowest_30d=parse_price(get("NAJNIŽA CIJENA U POSLJEDNIH 30 DANA")),
            barcode=clean_barcode(get("BARKOD")),
            anchor_price=parse_price(get("SIDRENA CIJENA NA 2.5.2025")),
        )
