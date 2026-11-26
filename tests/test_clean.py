import pytest

from tracker.clean import (
    clean_barcode,
    normalize_name,
    parse_price,
    parse_quantity,
    quantity_from_name,
)


@pytest.mark.parametrize("value, expected", [
    ("2.09", 2.09),
    ("2,09", 2.09),
    ("10", 10.0),
    (" 1.234,50 ", 1234.5),
    ("", None),
    ("abc", None),
    (None, None),
])
def test_parse_price(value, expected):
    assert parse_price(value) == expected


@pytest.mark.parametrize("text, expected", [
    ("0.25 l", (0.25, "l")),
    ("500ml", (0.5, "l")),
    ("85g", (0.085, "kg")),
    ("1.00 kg", (1.0, "kg")),
    ("1.00 ko", (1.0, "kom")),
    ("2,5 dl", (0.25, "l")),
    ("", None),
    (None, None),
])
def test_parse_quantity(text, expected):
    result = parse_quantity(text)
    if expected is None:
        assert result is None
    else:
        assert result[0] == pytest.approx(expected[0])
        assert result[1] == expected[1]


def test_quantity_from_name():
    assert quantity_from_name("NAPITAK NES XPRESS BLACK 250ml") == pytest.approx((0.25, "l"))
    assert quantity_from_name("MLIJEKO TRAJNO 2.8% DUKAT 1 L") == (1.0, "l")
    assert quantity_from_name("KRUH BIJELI") is None


def test_normalize_name():
    assert normalize_name("MLIJEKO  TRAJNO 2,8% DUKAT") == "mlijeko trajno 2.8% dukat"
    assert normalize_name("ČOKOLADA ŠLAG ĐUREK žuta Ć") == "cokolada slag durek zuta c"


def test_clean_barcode():
    assert clean_barcode("3850139541144") == "3850139541144"
    assert clean_barcode(" 3850139541144 ") == "3850139541144"
    assert clean_barcode("") is None
    assert clean_barcode("123") is None
    assert clean_barcode(None) is None
