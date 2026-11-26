# System architecture

## Goal

Every day the system downloads the public price lists published by Croatian retail chains,
converts them to a common format and stores them in a database, building a price history over
time. On top of that data the user can search products, compare prices across stores, follow
price changes and check whether a promotion is a real discount.

The downloader, parsers and data cleaning are our own code (no reliance on existing projects
such as cijene-api).

## Scope by checkpoint

| Checkpoint | Content |
|---|---|
| 1 | Konzum: download, parsing, cleaning, SQLite database, CLI commands (`search`, `history`, `compare`, `stats`), Croatian/English interface |
| 2 | Second chain, product matching without barcodes, promotion checks |
| 3 | Web interface (Flask + Chart.js), notifications, cheapest basket, statistics |

Out of scope: downloading all ~570 Konzum stores (too much data, ~1.4 GB per day). Stores are
selected in the settings by city. The initial selection is Rijeka: 5 stores (Osječka 71 SUPER,
Nikole Tesle 9, Riva 16, Vatroslava Lisinskog 2 and the online shop), all available days (~14).

## Data source: Konzum

- The page `https://www.konzum.hr/cjenici?date=YYYY-MM-DD&page=N` links to CSV files, one per
  store, for the last ~14 days.
- The file name contains the store type, address, store code and date, e.g.
  `20261126-SUPER,ŽITNA 1A 10310 IVANIĆ GRAD,0204,113241,26.11.2026, 05-24.CSV`.
- The CSV is UTF-8, ~26,000 rows and ~2.4 MB per store. Columns: name, code, brand, net
  quantity, unit, retail price, special sale (DA/NE), special sale name, unit price, barcode,
  base price.
- Konzum changed the format on 2026-11-17. The old format (until 2026-11-16) had separate
  columns for the promo price, the lowest price in the last 30 days and the anchor price on
  2025-05-02. The new format has a promo flag (DA/NE) and a "base price" instead. The parser
  detects the format from the header and maps both to the same record. When a chain does not
  publish the lowest 30-day price, it is computed from our own history.

## Data flow

```
source ──► fetch ──► data/raw/<chain>/<date>/*.csv.gz
                         │
                         ▼
                      parse  (one parser per chain → PriceRecord)
                         │
                         ▼
                      clean  (numbers, units, names, brand/quantity from name)
                         │
                         ▼
                      load ──► data/tracker.db (SQLite)
                         │
                ┌────────┴────────┐
                ▼                 ▼
          CLI commands       web (checkpoint 3)
```

- Raw files are stored compressed and never modified, so processing can be re-run without
  downloading again (important because chains delete price lists older than 30 days).
- Each step can be run on its own (`fetch`, `import`) or together (`run`).
- Import is idempotent: the `import_log` table records imported files.
- If the listing for one day or a single file fails, the rest is still downloaded.

## Chains

Each chain is a class derived from a common base class:

- `available_dates()` — dates for which price lists are published
- `discover(date)` — list of files (URL, store, date) for a given day
- `parse(path)` — reads a file and yields records in the common `PriceRecord` format
- `parse_store(filename)` — store details from the file name

A new chain = one new module + an entry in the chain registry.

## Database

```
chains ─< stores ─< prices >─ chain_products >─ products
                                     │
                              product_matches
```

- `chains` — retail chains
- `stores` — stores (code, type, address, city)
- `chain_products` — a product as listed by one chain (code, name, brand, net quantity, unit,
  barcode, normalized name, parsed quantity)
- `products` — the shared (canonical) product; currently linked by barcode
- `product_matches` — candidate matches without a barcode, with a score and a status
  (`pending` / `confirmed` / `rejected`); used from checkpoint 2
- `prices` — one row per day, store and product: price, unit price, promo flag and name, base
  price, lowest 30-day price and anchor price (when the chain publishes them)
- `import_log` — imported files, row count, time

## Cleaning

- decimal comma/point → `float`, empty values → `NULL`
- net quantity (`0.25 l`, `1.00 kg`, `500ml`) → amount + base unit (l, kg, kom)
- names: lowercase, collapsed whitespace, diacritics removed for comparison
- brand and quantity extracted from the name (groundwork for matching without barcodes)

## Interface language

All user-facing text lives in `tracker/i18n.py` in Croatian and English. The default is set
with `language` in `config.toml` (`hr`) and can be overridden per command with `--lang en`.
Prices and percentages follow the language convention (`1,79 €` / `€1.79`). Product names are
data and are shown as published.

## Technologies

| Purpose | Tool |
|---|---|
| language | Python 3.12 |
| HTTP | requests |
| HTML | BeautifulSoup |
| CSV | `csv` (standard library) |
| database | SQLite (`sqlite3`), plain SQL, no ORM |
| CLI | `argparse` |
| settings | `config.toml` (`tomllib`) |
| parallel downloads | `concurrent.futures.ThreadPoolExecutor` |
| tests | pytest |
| scheduling | cron |
| web (checkpoint 3) | Flask, Chart.js |

Considered and rejected: pandas (unnecessarily heavy for row-by-row reading), Scrapy (too big
for a single page of links), PostgreSQL (needs a separate server), storing only price changes
instead of daily rows (only worth it with a large number of stores).

## Project structure

```
hr-price-tracker/
├── tracker/
│   ├── __main__.py      CLI
│   ├── config.py
│   ├── i18n.py          Croatian/English texts
│   ├── fetch.py         downloading
│   ├── chains/
│   │   ├── base.py      base class, PriceRecord
│   │   └── konzum.py
│   ├── clean.py
│   ├── db.py            schema
│   ├── load.py          import into the database
│   └── queries.py       search, history, comparison, statistics
├── tests/
│   └── fixtures/
├── scripts/daily.sh
├── docs/
├── config.toml
├── requirements.txt
└── data/                (not in git)
```
