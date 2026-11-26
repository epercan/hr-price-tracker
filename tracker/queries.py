from tracker.clean import normalize_name

PRODUCT_FILTER = "(cp.code = :code OR cp.barcode = :code)"


def last_date(conn):
    return conn.execute("SELECT MAX(date) FROM prices").fetchone()[0]


def search(conn, term, limit=20):
    words = normalize_name(term).split()
    if not words:
        return []
    where = " AND ".join("cp.name_norm LIKE ?" for _ in words)
    return conn.execute(f"""
        SELECT cp.code, cp.name, cp.brand, cp.barcode,
               MIN(p.price) AS min_price, MAX(p.price) AS max_price
        FROM chain_products cp
        JOIN prices p ON p.chain_product_id = cp.id
        WHERE {where} AND p.date = ?
        GROUP BY cp.id
        ORDER BY cp.name
        LIMIT ?
    """, [f"%{w}%" for w in words] + [last_date(conn), limit]).fetchall()


def history(conn, code):
    return conn.execute(f"""
        SELECT p.date, MIN(p.price) AS min_price, MAX(p.price) AS max_price,
               MAX(p.is_promo) AS is_promo
        FROM prices p
        JOIN chain_products cp ON cp.id = p.chain_product_id
        WHERE {PRODUCT_FILTER}
        GROUP BY p.date
        ORDER BY p.date
    """, {"code": code}).fetchall()


def compare(conn, code):
    return conn.execute(f"""
        SELECT s.address, s.type, cp.name, p.price, p.unit_price, p.is_promo, p.base_price
        FROM prices p
        JOIN chain_products cp ON cp.id = p.chain_product_id
        JOIN stores s ON s.id = p.store_id
        WHERE {PRODUCT_FILTER} AND p.date = :day
        ORDER BY p.price, s.address
    """, {"code": code, "day": last_date(conn)}).fetchall()


def stats(conn):
    first, last = conn.execute("SELECT MIN(date), MAX(date) FROM prices").fetchone()
    one = lambda sql, *args: conn.execute(sql, args).fetchone()[0]
    result = {
        "stores": one("SELECT COUNT(*) FROM stores"),
        "products": one("SELECT COUNT(*) FROM chain_products"),
        "prices": one("SELECT COUNT(*) FROM prices"),
        "first_date": first,
        "last_date": last,
        "promo_share": one(
            "SELECT AVG(is_promo) * 100 FROM prices WHERE date = ?", last) or 0,
    }
    result["biggest_changes"] = conn.execute("""
        WITH a AS (SELECT chain_product_id, AVG(price) AS price FROM prices
                   WHERE date = ? GROUP BY chain_product_id),
             b AS (SELECT chain_product_id, AVG(price) AS price FROM prices
                   WHERE date = ? GROUP BY chain_product_id)
        SELECT cp.code, cp.name, a.price AS old_price, b.price AS new_price,
               (b.price - a.price) / a.price * 100 AS change_pct
        FROM a JOIN b USING (chain_product_id)
        JOIN chain_products cp ON cp.id = a.chain_product_id
        WHERE a.price > 0 AND a.price != b.price
        ORDER BY ABS(change_pct) DESC
        LIMIT 10
    """, (first, last)).fetchall()
    result["promo_above_base"] = conn.execute("""
        SELECT cp.code, cp.name, s.address, p.price, p.base_price
        FROM prices p
        JOIN chain_products cp ON cp.id = p.chain_product_id
        JOIN stores s ON s.id = p.store_id
        WHERE p.date = ? AND p.is_promo = 1 AND p.price > p.base_price
        ORDER BY p.price - p.base_price DESC
    """, (last,)).fetchall()
    return result
