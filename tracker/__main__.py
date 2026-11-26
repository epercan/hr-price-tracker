import argparse
import time

from tracker import i18n, queries
from tracker.chains import CHAINS
from tracker.config import load_config
from tracker.db import connect
from tracker.fetch import fetch
from tracker.i18n import eur, pct, t
from tracker.load import import_all


def print_table(rows, columns):
    if not rows:
        print(t("no_results"))
        return
    columns = [(t(key), fmt) for key, fmt in columns]
    widths = [max(len(title), *(len(str(fmt(r))) for r in rows)) for title, fmt in columns]
    print("  ".join(title.ljust(w) for (title, _), w in zip(columns, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(fmt(r)).ljust(w) for (_, fmt), w in zip(columns, widths)))


def yes(value):
    return t("yes") if value else ""


def cmd_fetch(cfg, args):
    settings = cfg["konzum"]
    start = time.time()
    result = fetch(CHAINS["konzum"](), cfg["data_dir"], settings.get("city"), settings["days"],
                   settings["workers"])
    print(t("fetch_done", secs=time.time() - start, **result))


def cmd_import(cfg, args):
    conn = connect(cfg["db_path"])
    start = time.time()
    result = import_all(conn, CHAINS["konzum"](), cfg["data_dir"])
    print(t("import_done", secs=time.time() - start, **result))


def cmd_run(cfg, args):
    cmd_fetch(cfg, args)
    cmd_import(cfg, args)


def cmd_search(cfg, args):
    rows = queries.search(connect(cfg["db_path"]), " ".join(args.term), args.limit)
    print_table(rows, [
        ("col_code", lambda r: r["code"]),
        ("col_name", lambda r: r["name"]),
        ("col_brand", lambda r: r["brand"] or ""),
        ("col_barcode", lambda r: r["barcode"] or ""),
        ("col_min", lambda r: eur(r["min_price"])),
        ("col_max", lambda r: eur(r["max_price"])),
    ])


def cmd_history(cfg, args):
    rows = queries.history(connect(cfg["db_path"]), args.code)
    print_table(rows, [
        ("col_date", lambda r: r["date"]),
        ("col_min", lambda r: eur(r["min_price"])),
        ("col_max", lambda r: eur(r["max_price"])),
        ("col_promo", lambda r: yes(r["is_promo"])),
    ])


def cmd_compare(cfg, args):
    rows = queries.compare(connect(cfg["db_path"]), args.code)
    if rows:
        print(rows[0]["name"])
    print_table(rows, [
        ("col_store", lambda r: f"{r['address']} ({r['type']})"),
        ("col_price", lambda r: eur(r["price"])),
        ("col_unit_price", lambda r: eur(r["unit_price"])),
        ("col_promo", lambda r: yes(r["is_promo"])),
        ("col_base", lambda r: eur(r["base_price"])),
    ])


def cmd_stats(cfg, args):
    s = queries.stats(connect(cfg["db_path"]))
    print(t("stats_stores", n=s["stores"]))
    print(t("stats_products", n=s["products"]))
    print(t("stats_prices", n=s["prices"]))
    print(t("stats_period", first=s["first_date"], last=s["last_date"]))
    print(t("stats_promo_share", day=s["last_date"], share=pct(s["promo_share"])))
    print("\n" + t("stats_changes", first=s["first_date"], last=s["last_date"]))
    print_table(s["biggest_changes"], [
        ("col_name", lambda r: r["name"]),
        ("col_before", lambda r: eur(r["old_price"])),
        ("col_now", lambda r: eur(r["new_price"])),
        ("col_change", lambda r: pct(r["change_pct"], sign=True)),
    ])
    suspicious = s["promo_above_base"]
    print("\n" + t("stats_above_base", n=len(suspicious)))
    print_table(suspicious[:10], [
        ("col_name", lambda r: r["name"]),
        ("col_store", lambda r: r["address"]),
        ("col_promo", lambda r: eur(r["price"])),
        ("col_base", lambda r: eur(r["base_price"])),
    ])


def build_parser():
    parser = argparse.ArgumentParser(prog="tracker", description=t("description"))
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--lang", choices=list(i18n.MESSAGES), help=t("help_lang"))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help=t("help_fetch")).set_defaults(func=cmd_fetch)
    sub.add_parser("import", help=t("help_import")).set_defaults(func=cmd_import)
    sub.add_parser("run", help=t("help_run")).set_defaults(func=cmd_run)

    p = sub.add_parser("search", help=t("help_search"))
    p.add_argument("term", nargs="+")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    for name, func in [("history", cmd_history), ("compare", cmd_compare)]:
        p = sub.add_parser(name, help=t(f"help_{name}"))
        p.add_argument("code", help=t("help_code"))
        p.set_defaults(func=func)

    sub.add_parser("stats", help=t("help_stats")).set_defaults(func=cmd_stats)
    return parser


def main(argv=None):
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", default="config.toml")
    pre.add_argument("--lang", choices=list(i18n.MESSAGES))
    known, _ = pre.parse_known_args(argv)
    try:
        cfg = load_config(known.config)
    except FileNotFoundError:
        cfg = None
    i18n.set_language(known.lang or (cfg or {}).get("language", "hr"))

    args = build_parser().parse_args(argv)
    if cfg is None:
        cfg = load_config(args.config)
    args.func(cfg, args)


if __name__ == "__main__":
    main()
