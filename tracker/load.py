from datetime import datetime

from tracker.i18n import t
from tracker.clean import normalize_name, parse_quantity, quantity_from_name


def _get_id(conn, sql, params):
    return conn.execute(sql, params).fetchone()[0]


def _chain_id(conn, name):
    return _get_id(conn, """
        INSERT INTO chains (name) VALUES (?)
        ON CONFLICT (name) DO UPDATE SET name = excluded.name RETURNING id
    """, (name,))


def _store_id(conn, chain_id, store):
    return _get_id(conn, """
        INSERT INTO stores (chain_id, code, type, address, postcode, city)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (chain_id, code) DO UPDATE SET
            type = excluded.type, address = excluded.address,
            postcode = excluded.postcode, city = excluded.city
        RETURNING id
    """, (chain_id, store.code, store.type, store.address, store.postcode, store.city))


def _product_id(conn, barcode, name):
    if not barcode:
        return None
    return _get_id(conn, """
        INSERT INTO products (barcode, name) VALUES (?, ?)
        ON CONFLICT (barcode) DO UPDATE SET barcode = excluded.barcode RETURNING id
    """, (barcode, name))


def _chain_product_id(conn, chain_id, rec):
    qty = parse_quantity(rec.net_quantity) or quantity_from_name(rec.name) or (None, None)
    return _get_id(conn, """
        INSERT INTO chain_products
            (chain_id, code, name, name_norm, brand, net_quantity, unit, qty, qty_unit,
             barcode, product_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (chain_id, code) DO UPDATE SET
            name = excluded.name, name_norm = excluded.name_norm, brand = excluded.brand,
            net_quantity = excluded.net_quantity, unit = excluded.unit, qty = excluded.qty,
            qty_unit = excluded.qty_unit, barcode = excluded.barcode,
            product_id = excluded.product_id
        RETURNING id
    """, (chain_id, rec.product_code, rec.name, normalize_name(rec.name), rec.brand,
          rec.net_quantity, rec.unit, qty[0], qty[1], rec.barcode,
          _product_id(conn, rec.barcode, rec.name)))


def import_file(conn, chain, path):
    if conn.execute("SELECT 1 FROM import_log WHERE path = ?", (str(path),)).fetchone():
        return None

    filename = path.name.removesuffix(".gz")
    day = datetime.strptime(filename[:8], "%Y%m%d").date().isoformat()
    rows = 0
    with conn:
        chain_id = _chain_id(conn, chain.name)
        store_id = _store_id(conn, chain_id, chain.parse_store(filename))
        for rec in chain.parse(path):
            if rec.price is None:
                continue
            cp_id = _chain_product_id(conn, chain_id, rec)
            cur = conn.execute("""
                INSERT OR IGNORE INTO prices
                    (store_id, chain_product_id, date, price, unit_price, is_promo,
                     promo_name, base_price, lowest_30d, anchor_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (store_id, cp_id, day, rec.price, rec.unit_price, int(rec.is_promo),
                  rec.promo_name, rec.base_price, rec.lowest_30d, rec.anchor_price))
            rows += cur.rowcount
        conn.execute(
            "INSERT INTO import_log (path, chain_id, store_id, date, rows) VALUES (?, ?, ?, ?, ?)",
            (str(path), chain_id, store_id, day, rows),
        )
    return rows


def import_all(conn, chain, data_dir):
    result = {"files": 0, "rows": 0, "skipped": 0}
    for path in sorted((data_dir / "raw" / chain.name).glob("*/*.gz")):
        rows = import_file(conn, chain, path)
        if rows is None:
            result["skipped"] += 1
        else:
            result["files"] += 1
            result["rows"] += rows
            print(t("file_imported", day=path.parent.name, name=path.name[:40], rows=rows))
    return result
