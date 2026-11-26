MESSAGES = {
    "hr": {
        "description": "Praćenje cijena u trgovačkim lancima",
        "help_fetch": "preuzmi cjenike",
        "help_import": "uvezi preuzete cjenike u bazu",
        "help_run": "preuzmi i uvezi",
        "help_search": "pretraži proizvode",
        "help_history": "kretanje cijene po danima",
        "help_compare": "cijena po poslovnicama",
        "help_code": "šifra proizvoda ili barkod",
        "help_stats": "statistika",
        "help_lang": "jezik ispisa (hr ili en)",
        "no_results": "Nema rezultata.",
        "day_files": "{day}: {count} cjenika",
        "day_error": "{day}: greška kod dohvaćanja popisa: {error}",
        "file_error": "Greška kod {name}: {error}",
        "file_imported": "{day} {name}... {rows} cijena",
        "fetch_done": "Preuzeto: {downloaded}, preskočeno: {skipped}, greške: {failed} ({secs:.0f} s)",
        "import_done": "Uvezeno datoteka: {files}, cijena: {rows}, preskočeno: {skipped} ({secs:.0f} s)",
        "col_code": "Šifra",
        "col_name": "Naziv",
        "col_brand": "Marka",
        "col_barcode": "Barkod",
        "col_min": "Min",
        "col_max": "Max",
        "col_date": "Datum",
        "col_promo": "Akcija",
        "col_store": "Poslovnica",
        "col_price": "Cijena",
        "col_unit_price": "Po jedinici",
        "col_base": "Bazna",
        "col_before": "Prije",
        "col_now": "Sada",
        "col_change": "Promjena",
        "yes": "da",
        "stats_stores": "Poslovnica: {n}",
        "stats_products": "Proizvoda: {n}",
        "stats_prices": "Zapisa cijena: {n}",
        "stats_period": "Razdoblje: {first} – {last}",
        "stats_promo_share": "Udio proizvoda na akciji ({day}): {share}",
        "stats_changes": "Najveće promjene cijene ({first} → {last}):",
        "stats_above_base": "Akcije s cijenom višom od bazne: {n}",
    },
    "en": {
        "description": "Price tracking for retail chains",
        "help_fetch": "download price lists",
        "help_import": "import downloaded price lists into the database",
        "help_run": "download and import",
        "help_search": "search products",
        "help_history": "price history by day",
        "help_compare": "price by store",
        "help_code": "product code or barcode",
        "help_stats": "statistics",
        "help_lang": "output language (hr or en)",
        "no_results": "No results.",
        "day_files": "{day}: {count} price lists",
        "day_error": "{day}: failed to fetch listing: {error}",
        "file_error": "Error downloading {name}: {error}",
        "file_imported": "{day} {name}... {rows} prices",
        "fetch_done": "Downloaded: {downloaded}, skipped: {skipped}, errors: {failed} ({secs:.0f} s)",
        "import_done": "Imported files: {files}, prices: {rows}, skipped: {skipped} ({secs:.0f} s)",
        "col_code": "Code",
        "col_name": "Name",
        "col_brand": "Brand",
        "col_barcode": "Barcode",
        "col_min": "Min",
        "col_max": "Max",
        "col_date": "Date",
        "col_promo": "Promo",
        "col_store": "Store",
        "col_price": "Price",
        "col_unit_price": "Per unit",
        "col_base": "Base",
        "col_before": "Before",
        "col_now": "Now",
        "col_change": "Change",
        "yes": "yes",
        "stats_stores": "Stores: {n}",
        "stats_products": "Products: {n}",
        "stats_prices": "Price records: {n}",
        "stats_period": "Period: {first} – {last}",
        "stats_promo_share": "Share of products on promotion ({day}): {share}",
        "stats_changes": "Biggest price changes ({first} → {last}):",
        "stats_above_base": "Promotions priced above base price: {n}",
    },
}

language = "hr"


def set_language(lang):
    global language
    if lang not in MESSAGES:
        raise ValueError(f"Unsupported language: {lang}")
    language = lang


def t(key, **kwargs):
    return MESSAGES[language][key].format(**kwargs)


def eur(value):
    if value is None:
        return "-"
    if language == "hr":
        return f"{value:.2f} €".replace(".", ",")
    return f"€{value:.2f}"


def pct(value, sign=False):
    text = f"{value:+.1f}" if sign else f"{value:.1f}"
    if language == "hr":
        return text.replace(".", ",") + " %"
    return text + "%"
