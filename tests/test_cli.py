from tests.conftest import RIJEKA, write_raw
from tracker.__main__ import main


def write_config(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('data_dir = "data"\ndb_path = "data/t.db"\n'
                   '[konzum]\ncity = "RIJEKA"\ndays = 14\nworkers = 1\n')
    return cfg


def test_cli_import_and_search(tmp_path, capsys):
    cfg = write_config(tmp_path)
    write_raw(tmp_path / "data", RIJEKA)
    main(["--config", str(cfg), "import"])
    main(["--config", str(cfg), "search", "nes", "black"])
    out = capsys.readouterr().out
    assert "NAPITAK NES XPRESS BLACK 250ml" in out
    assert "1,79 €" in out


def test_cli_search_no_results(tmp_path, capsys):
    cfg = write_config(tmp_path)
    write_raw(tmp_path / "data", RIJEKA)
    main(["--config", str(cfg), "import"])
    main(["--config", str(cfg), "search", "xyzxyz"])
    assert "Nema rezultata." in capsys.readouterr().out
