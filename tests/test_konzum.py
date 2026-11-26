import gzip
from datetime import date
from pathlib import Path

from tracker.chains.base import Store
from tracker.chains.konzum import KonzumChain, parse_dates, parse_links, parse_store

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "konzum_sample.csv"
FILENAME = "20261126-SUPER,OSJEČKA 71 51000 RIJEKA,3271,113704,26.11.2026, 05-26.CSV"


def test_parse_store():
    assert parse_store(FILENAME) == Store(
        code="3271", type="SUPER", address="OSJEČKA 71", postcode="51000", city="RIJEKA"
    )


def test_parse_links_from_fixture():
    links = parse_links((FIXTURES / "konzum_page.html").read_text(encoding="utf-8"))
    assert len(links) == 3
    assert all(l.startswith("https://") and l.endswith(".CSV") for l in links)


def test_parse_links_empty_page():
    assert parse_links("<html></html>") == []


def test_parse_dates():
    html = (FIXTURES / "konzum_page.html").read_text(encoding="utf-8")
    assert parse_dates(html) == [date(2026, 11, 25), date(2026, 11, 26)]


def _records(path):
    return list(KonzumChain().parse(path))


def test_parse_sample_csv():
    records = _records(SAMPLE)
    lines = SAMPLE.read_text(encoding="utf-8").splitlines()
    assert len(records) == len(lines) - 1

    pom = next(r for r in records if "POMSTICKS" in r.name)
    assert pom.is_promo is True
    assert pom.price == 2.09
    assert pom.base_price == 1.99
    assert pom.lowest_30d is None

    assert next(r for r in records if r.name.startswith("VANILIN")).barcode is None
    assert next(r for r in records if r.name.startswith("ŽEMLJA")).price is None


def test_parse_gzip(tmp_path):
    gz = tmp_path / "sample.csv.gz"
    gz.write_bytes(gzip.compress(SAMPLE.read_bytes()))
    assert len(_records(gz)) == len(_records(SAMPLE))


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, pages):
        self.pages = pages
        self.urls = []

    def get(self, url, params=None, timeout=None):
        self.urls.append(params)
        return FakeResponse(self.pages[params["page"] - 1] if params["page"] <= len(self.pages) else "")


def test_discover_walks_pages_until_no_new_links():
    page = (FIXTURES / "konzum_page.html").read_text(encoding="utf-8")
    session = FakeSession([page, page])
    refs = KonzumChain(session=session).discover(date(2026, 11, 26))
    assert len(refs) == 3
    assert {r.store.city for r in refs} == {"IVANIĆ GRAD", "RIJEKA"}
    assert refs[0].date == date(2026, 11, 26)
    assert len(session.urls) == 2


def test_parse_old_format():
    records = _records(FIXTURES / "konzum_sample_old.csv")
    assert len(records) == 12
    keks = next(r for r in records if r.name.startswith("KEKS DOMAĆICA MEDENJACI"))
    assert keks.is_promo is True
    assert keks.price == 2.49
    assert keks.lowest_30d == 3.49
    assert keks.anchor_price == 3.49
    regular = records[0]
    assert regular.is_promo is False
    assert regular.price == 0.99
    assert regular.lowest_30d is None
