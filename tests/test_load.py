import pytest

from tests.conftest import RIVA, SAMPLE, write_raw
from tracker.chains.konzum import KonzumChain
from tracker.db import connect
from tracker.load import import_all, import_file


@pytest.fixture
def conn(tmp_path):
    return connect(tmp_path / "test.db")


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def priced_rows():
    return len({r.product_code for r in KonzumChain().parse(SAMPLE) if r.price is not None})


def test_import_file_counts(conn, raw_file):
    assert import_file(conn, KonzumChain(), raw_file) == priced_rows()
    assert count(conn, "prices") == priced_rows()
    store = conn.execute("SELECT * FROM stores").fetchone()
    assert (store["code"], store["city"]) == ("3271", "RIJEKA")


def test_import_is_idempotent(conn, raw_file):
    import_file(conn, KonzumChain(), raw_file)
    assert import_file(conn, KonzumChain(), raw_file) is None
    assert count(conn, "prices") == priced_rows()


def test_products_linked_by_barcode(conn, tmp_path, raw_file):
    import_file(conn, KonzumChain(), raw_file)
    import_file(conn, KonzumChain(), write_raw(tmp_path, RIVA))
    row = conn.execute("""
        SELECT COUNT(DISTINCT p.store_id) AS stores, COUNT(DISTINCT pr.id) AS products
        FROM prices p
        JOIN chain_products cp ON cp.id = p.chain_product_id
        JOIN products pr ON pr.id = cp.product_id
        WHERE cp.barcode = '8445290619167'
    """).fetchone()
    assert (row["stores"], row["products"]) == (2, 1)


def test_quantity_filled(conn, raw_file):
    import_file(conn, KonzumChain(), raw_file)
    row = conn.execute(
        "SELECT qty, qty_unit FROM chain_products WHERE name = 'NAPITAK NES XPRESS BLACK 250ml'"
    ).fetchone()
    assert row["qty"] == pytest.approx(0.25)
    assert row["qty_unit"] == "l"


def test_import_all(conn, tmp_path, raw_file):
    write_raw(tmp_path, RIVA)
    result = import_all(conn, KonzumChain(), tmp_path)
    assert result == {"files": 2, "rows": 2 * priced_rows(), "skipped": 0}
    assert import_all(conn, KonzumChain(), tmp_path)["skipped"] == 2
