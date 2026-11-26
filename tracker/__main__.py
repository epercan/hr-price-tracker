import argparse
import time

from tracker import queries
from tracker.chains import CHAINS
from tracker.config import load_config
from tracker.db import connect
from tracker.fetch import fetch
from tracker.load import import_all


def eur(value):
    if value is None:
        return "-"
    return f"{value:.2f} €".replace(".", ",")


def pct(value, sign=False):
    return (f"{value:+.1f} %" if sign else f"{value:.1f} %").replace(".", ",")


def print_table(rows, columns):
    if not rows:
        print("Nema rezultata.")
        return
    widths = [max(len(title), *(len(str(fmt(r))) for r in rows)) for title, fmt in columns]
    print("  ".join(title.ljust(w) for (title, _), w in zip(columns, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(fmt(r)).ljust(w) for (_, fmt), w in zip(columns, widths)))


def cmd_fetch(cfg, args):
    settings = cfg["konzum"]
    chain = CHAINS["konzum"]()
    start = time.time()
    result = fetch(chain, cfg["data_dir"], settings.get("city"), settings["days"],
                   settings["workers"])
    print(f"Preuzeto: {result['downloaded']}, preskočeno: {result['skipped']}, "
          f"greške: {result['failed']} ({time.time() - start:.0f} s)")


def cmd_import(cfg, args):
    conn = connect(cfg["db_path"])
    start = time.time()
    result = import_all(conn, CHAINS["konzum"](), cfg["data_dir"])
    print(f"Uvezeno datoteka: {result['files']}, cijena: {result['rows']}, "
          f"preskočeno: {result['skipped']} ({time.time() - start:.0f} s)")


def cmd_run(cfg, args):
    cmd_fetch(cfg, args)
    cmd_import(cfg, args)


def cmd_search(cfg, args):
    rows = queries.search(connect(cfg["db_path"]), " ".join(args.term), args.limit)
    print_table(rows, [
        ("Šifra", lambda r: r["code"]),
        ("Naziv", lambda r: r["name"]),
        ("Marka", lambda r: r["brand"] or ""),
        ("Barkod", lambda r: r["barcode"] or ""),
        ("Min", lambda r: eur(r["min_price"])),
        ("Max", lambda r: eur(r["max_price"])),
    ])


def cmd_history(cfg, args):
    rows = queries.history(connect(cfg["db_path"]), args.code)
    print_table(rows, [
        ("Datum", lambda r: r["date"]),
        ("Min", lambda r: eur(r["min_price"])),
        ("Max", lambda r: eur(r["max_price"])),
        ("Akcija", lambda r: "da" if r["is_promo"] else ""),
    ])


def cmd_compare(cfg, args):
    rows = queries.compare(connect(cfg["db_path"]), args.code)
    if rows:
        print(rows[0]["name"])
    print_table(rows, [
        ("Poslovnica", lambda r: f"{r['address']} ({r['type']})"),
        ("Cijena", lambda r: eur(r["price"])),
        ("Po jedinici", lambda r: eur(r["unit_price"])),
        ("Akcija", lambda r: "da" if r["is_promo"] else ""),
        ("Bazna", lambda r: eur(r["base_price"])),
    ])


def cmd_stats(cfg, args):
    s = queries.stats(connect(cfg["db_path"]))
    print(f"Poslovnica: {s['stores']}")
    print(f"Proizvoda: {s['products']}")
    print(f"Zapisa cijena: {s['prices']}")
    print(f"Razdoblje: {s['first_date']} – {s['last_date']}")
    print(f"Udio proizvoda na akciji ({s['last_date']}): {pct(s['promo_share'])}")
    print(f"\nNajveće promjene cijene ({s['first_date']} → {s['last_date']}):")
    print_table(s["biggest_changes"], [
        ("Naziv", lambda r: r["name"]),
        ("Prije", lambda r: eur(r["old_price"])),
        ("Sada", lambda r: eur(r["new_price"])),
        ("Promjena", lambda r: pct(r["change_pct"], sign=True)),
    ])
    suspicious = s["promo_above_base"]
    print(f"\nAkcije s cijenom višom od bazne: {len(suspicious)}")
    print_table(suspicious[:10], [
        ("Naziv", lambda r: r["name"]),
        ("Poslovnica", lambda r: r["address"]),
        ("Akcija", lambda r: eur(r["price"])),
        ("Bazna", lambda r: eur(r["base_price"])),
    ])


def build_parser():
    parser = argparse.ArgumentParser(prog="tracker", description="Praćenje cijena u trgovinama")
    parser.add_argument("--config", default="config.toml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="preuzmi cjenike").set_defaults(func=cmd_fetch)
    sub.add_parser("import", help="uvezi preuzete cjenike u bazu").set_defaults(func=cmd_import)
    sub.add_parser("run", help="preuzmi i uvezi").set_defaults(func=cmd_run)

    p = sub.add_parser("search", help="pretraži proizvode")
    p.add_argument("term", nargs="+")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    for name, func, text in [("history", cmd_history, "kretanje cijene po danima"),
                             ("compare", cmd_compare, "cijena po poslovnicama")]:
        p = sub.add_parser(name, help=text)
        p.add_argument("code", help="šifra proizvoda ili barkod")
        p.set_defaults(func=func)

    sub.add_parser("stats", help="statistika").set_defaults(func=cmd_stats)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(load_config(args.config), args)


if __name__ == "__main__":
    main()
