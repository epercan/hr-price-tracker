import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS chains (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY,
    chain_id INTEGER NOT NULL REFERENCES chains(id),
    code TEXT NOT NULL,
    type TEXT,
    address TEXT,
    postcode TEXT,
    city TEXT,
    UNIQUE (chain_id, code)
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE,
    name TEXT
);
CREATE TABLE IF NOT EXISTS chain_products (
    id INTEGER PRIMARY KEY,
    chain_id INTEGER NOT NULL REFERENCES chains(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    name_norm TEXT NOT NULL,
    brand TEXT,
    net_quantity TEXT,
    unit TEXT,
    qty REAL,
    qty_unit TEXT,
    barcode TEXT,
    product_id INTEGER REFERENCES products(id),
    UNIQUE (chain_id, code)
);
CREATE TABLE IF NOT EXISTS product_matches (
    id INTEGER PRIMARY KEY,
    chain_product_id INTEGER NOT NULL REFERENCES chain_products(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    score REAL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'rejected'))
);
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id),
    chain_product_id INTEGER NOT NULL REFERENCES chain_products(id),
    date TEXT NOT NULL,
    price REAL NOT NULL,
    unit_price REAL,
    is_promo INTEGER NOT NULL DEFAULT 0,
    promo_name TEXT,
    base_price REAL,
    lowest_30d REAL,
    anchor_price REAL,
    UNIQUE (store_id, chain_product_id, date)
);
CREATE TABLE IF NOT EXISTS import_log (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    chain_id INTEGER REFERENCES chains(id),
    store_id INTEGER REFERENCES stores(id),
    date TEXT,
    rows INTEGER,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_prices_product_date ON prices (chain_product_id, date);
CREATE INDEX IF NOT EXISTS idx_cp_name_norm ON chain_products (name_norm);
CREATE INDEX IF NOT EXISTS idx_cp_barcode ON chain_products (barcode);
"""


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    return conn
