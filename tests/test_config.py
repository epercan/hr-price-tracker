from tracker.config import load_config


def test_load_config_resolves_paths(tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        'data_dir = "data"\ndb_path = "data/tracker.db"\n'
        '[konzum]\ncity = "RIJEKA"\ndays = 14\nworkers = 4\n'
    )
    cfg = load_config(cfg_file)
    assert cfg["db_path"] == tmp_path / "data/tracker.db"
    assert cfg["data_dir"] == tmp_path / "data"
    assert cfg["konzum"]["city"] == "RIJEKA"
