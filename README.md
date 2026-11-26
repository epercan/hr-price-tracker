# hr-price-tracker

A system for collecting, analysing and comparing product prices in Croatian retail chains.
Every day it downloads the publicly published price lists, converts them to a common format
and stores them in an SQLite database, building a price history. On top of that data you can
search products, compare prices across stores and follow price changes over time.

Project for the Scripting Languages course. The architecture is described in
[docs/architecture.md](docs/architecture.md).

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Settings (language, city, number of days, paths) are in `config.toml`. Konzum stores in
Rijeka are currently tracked.

## Usage

```bash
python -m tracker fetch            # download price lists (data/raw/)
python -m tracker import           # import downloaded price lists (data/tracker.db)
python -m tracker run              # fetch + import

python -m tracker search trajno mlijeko dukat
python -m tracker history 3850102019526     # product code or barcode
python -m tracker compare 3850102019526
python -m tracker stats
```

The interface is available in Croatian (default) and English. The default is set with
`language` in `config.toml`; a single command can be run in English with `--lang en`:

```
$ python -m tracker --lang en history 3850102019526
Date        Min    Max    Promo
----------  -----  -----  -----
2026-11-12  €2.49  €2.49  yes
...
2026-11-17  €3.49  €3.49
...
2026-11-24  €2.49  €3.49  yes
2026-11-25  €2.49  €2.49  yes
```

Running `fetch` and `import` again does not duplicate data: files already downloaded are
skipped and imported files are recorded in the `import_log` table.

## Scheduling

Price lists are published every morning by 8 am. To download them daily, add to `crontab -e`:

```
0 9 * * * /path/to/hr-price-tracker/scripts/daily.sh
```

Output is written to `data/daily.log`.

## Tests

```bash
pytest
```
