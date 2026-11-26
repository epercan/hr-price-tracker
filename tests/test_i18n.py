import pytest

from tracker import i18n


def test_both_languages_have_same_keys():
    assert i18n.MESSAGES["hr"].keys() == i18n.MESSAGES["en"].keys()


@pytest.mark.parametrize("lang, price, percent", [
    ("hr", "1,79 €", "+11,7 %"),
    ("en", "€1.79", "+11.7%"),
])
def test_number_formats(lang, price, percent):
    i18n.set_language(lang)
    assert i18n.eur(1.79) == price
    assert i18n.pct(11.66, sign=True) == percent
    i18n.set_language("hr")


def test_unknown_language_rejected():
    with pytest.raises(ValueError):
        i18n.set_language("de")
