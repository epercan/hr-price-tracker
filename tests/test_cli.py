from tests.conftest import RIJEKA, write_raw
from tracker.__main__ import main


def write_config(tmp_path, language=None):
    cfg = tmp_path / "config.toml"
    lang_line = f'language = "{language}"\n' if language else ""
    cfg.write_text(lang_line + 'data_dir = "data"\ndb_path = "data/t.db"\n'
                   '[konzum]\ncity = "RIJEKA"\ndays = 14\nworkers = 1\n')
    write_raw(tmp_path / "data", RIJEKA)
    return cfg


def run(cfg, *args):
    main(["--config", str(cfg), "import"])
    main(["--config", str(cfg), *args])


def test_search_croatian_by_default(tmp_path, capsys):
    run(write_config(tmp_path), "search", "nes", "black")
    out = capsys.readouterr().out
    assert "NAPITAK NES XPRESS BLACK 250ml" in out
    assert "1,79 €" in out
    assert "Naziv" in out


def test_search_english_with_flag(tmp_path, capsys):
    run(write_config(tmp_path), "--lang", "en", "search", "nes", "black")
    out = capsys.readouterr().out
    assert "€1.79" in out
    assert "Name" in out


def test_language_from_config(tmp_path, capsys):
    run(write_config(tmp_path, language="en"), "search", "xyzxyz")
    assert "No results." in capsys.readouterr().out


def test_no_results_croatian(tmp_path, capsys):
    run(write_config(tmp_path), "search", "xyzxyz")
    assert "Nema rezultata." in capsys.readouterr().out


def test_help_in_english(tmp_path, capsys):
    import pytest
    with pytest.raises(SystemExit):
        main(["--config", str(write_config(tmp_path)), "--lang", "en", "--help"])
    assert "Price tracking for retail chains" in capsys.readouterr().out
