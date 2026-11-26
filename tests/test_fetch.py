import gzip
from datetime import date

import requests

from tracker.chains.base import FileRef, Store
from tracker.fetch import download, fetch, raw_path


def make_ref(name, city):
    store = Store(code=name, type="SUPER", address="X 1", postcode="51000", city=city)
    return FileRef(url=f"https://cdn/{name}.CSV", filename=f"{name}.CSV",
                   date=date(2026, 11, 26), store=store)


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, fail=()):
        self.fail = set(fail)
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        if url in self.fail:
            raise requests.HTTPError("404")
        return FakeResponse(b"NAZIV;CIJENA\nmlijeko;1.09\n")


class FakeChain:
    name = "fake"

    def __init__(self, refs, session):
        self.refs = refs
        self.session = session

    def available_dates(self):
        return [date(2026, 11, 26)]

    def discover(self, day):
        return self.refs


def test_raw_path(tmp_path):
    ref = make_ref("a", "RIJEKA")
    assert raw_path(tmp_path, "konzum", ref) == tmp_path / "raw/konzum/2026-11-26/a.CSV.gz"


def test_download_writes_gzip(tmp_path):
    dest = tmp_path / "x" / "a.CSV.gz"
    assert download(FakeSession(), make_ref("a", "RIJEKA"), dest) is True
    with gzip.open(dest, "rb") as f:
        assert f.read() == b"NAZIV;CIJENA\nmlijeko;1.09\n"


def test_download_skips_existing(tmp_path):
    dest = tmp_path / "a.CSV.gz"
    session = FakeSession()
    download(session, make_ref("a", "RIJEKA"), dest)
    assert download(session, make_ref("a", "RIJEKA"), dest) is False
    assert len(session.calls) == 1


def test_fetch_filters_city_and_counts_failures(tmp_path, monkeypatch):
    monkeypatch.setattr("tracker.fetch.RETRY_DELAY", 0)
    refs = [make_ref("ok", "RIJEKA"), make_ref("bad", "RIJEKA"), make_ref("zg", "ZAGREB")]
    session = FakeSession(fail={"https://cdn/bad.CSV"})
    chain = FakeChain(refs, session)
    result = fetch(chain, tmp_path, city="RIJEKA", days=14, workers=2)
    assert result == {"downloaded": 1, "skipped": 0, "failed": 1}
    assert "https://cdn/zg.CSV" not in session.calls


def test_fetch_continues_when_day_listing_fails(tmp_path):
    class FlakyChain(FakeChain):
        def available_dates(self):
            return [date(2026, 11, 25), date(2026, 11, 26)]

        def discover(self, day):
            if day == date(2026, 11, 25):
                raise requests.ConnectionError("timeout")
            return self.refs

    chain = FlakyChain([make_ref("ok", "RIJEKA")], FakeSession())
    result = fetch(chain, tmp_path, city="RIJEKA", days=14, workers=1)
    assert result == {"downloaded": 1, "skipped": 0, "failed": 1}
