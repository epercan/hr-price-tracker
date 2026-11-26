import re
import unicodedata

UNITS = {
    "ml": (0.001, "l"), "cl": (0.01, "l"), "dl": (0.1, "l"), "l": (1, "l"),
    "g": (0.001, "kg"), "dkg": (0.01, "kg"), "kg": (1, "kg"),
    "kom": (1, "kom"), "ko": (1, "kom"),
}

QUANTITY_RE = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(dkg|kg|kom|ko|ml|cl|dl|l|g)\b", re.IGNORECASE
)


def parse_price(value):
    if value is None:
        return None
    value = value.strip()
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def _to_base(number, unit):
    factor, base = UNITS[unit.lower()]
    return round(float(number.replace(",", ".")) * factor, 6), base


def parse_quantity(text):
    if not text:
        return None
    m = QUANTITY_RE.search(text)
    if not m:
        return None
    return _to_base(m.group(1), m.group(2))


def quantity_from_name(name):
    matches = QUANTITY_RE.findall(name or "")
    if not matches:
        return None
    return _to_base(*matches[-1])


def normalize_name(name):
    name = name.lower().replace("đ", "d")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"(\d),(\d)", r"\1.\2", name)
    return " ".join(name.split())


def clean_barcode(value):
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if 8 <= len(digits) <= 14:
        return digits
    return None
