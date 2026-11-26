import pytest

from tests.conftest import RIJEKA, RIVA, SAMPLE, write_raw
from tracker.chains.konzum import KonzumChain
from tracker.db import connect
from tracker.load import import_all
from tracker.queries import compare, history, search, stats

XPRESS = "NAPITAK NES XPRESS BLACK 250ml,90391134,NESCAFE,0.25 l,ko,1.79,"


def with_xpress_price(price):
    return SAMPLE.read_text(encoding="utf-8").replace(XPRESS, XPRESS.replace("1.79", price))


@pytest.fixture
def conn(tmp_path):
    write_raw(tmp_path, RIJEKA.replace("20261126", "20261125"), with_xpress_price("1.99"),
              day="2026-11-25")
    write_raw(tmp_path, RIJEKA)
    write_raw(tmp_path, RIVA, with_xpress_price("1.69"))
    conn = connect(tmp_path / "test.db")
    import_all(conn, KonzumChain(), tmp_path)
    return conn


def test_search_without_diacritics(conn):
    names = [r["name"] for r in search(conn, "cokolada")]
    assert "ČOKOLADA LINDT EX CREAMY DARK 80 g" in names


def test_search_multiple_words(conn):
    rows = search(conn, "nes black")
    assert [r["name"] for r in rows] == ["NAPITAK NES XPRESS BLACK 250ml"]
    assert (rows[0]["min_price"], rows[0]["max_price"]) == (1.69, 1.79)


def test_search_no_results(conn):
    assert search(conn, "nepostojeciproizvod") == []


def test_history_two_dates(conn):
    rows = history(conn, "8445290619167")
    assert [(r["date"], r["min_price"], r["max_price"]) for r in rows] == [
        ("2026-11-25", 1.99, 1.99),
        ("2026-11-26", 1.69, 1.79),
    ]
    assert history(conn, "90391134") == rows


def test_compare_sorted_by_price(conn):
    rows = compare(conn, "90391134")
    assert [(r["address"], r["price"]) for r in rows] == [("RIVA 16", 1.69), ("OSJEČKA 71", 1.79)]


def test_stats_counts_promo_above_base(conn):
    s = stats(conn)
    assert s["stores"] == 2
    assert (s["first_date"], s["last_date"]) == ("2026-11-25", "2026-11-26")
    assert any("POMSTICKS" in r["name"] for r in s["promo_above_base"])
    top = s["biggest_changes"][0]
    assert top["name"] == "NAPITAK NES XPRESS BLACK 250ml"
    assert top["change_pct"] == pytest.approx((1.74 - 1.99) / 1.99 * 100)
