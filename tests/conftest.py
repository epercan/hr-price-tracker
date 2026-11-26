import gzip
from pathlib import Path

import pytest

SAMPLE = Path(__file__).parent / "fixtures" / "konzum_sample.csv"
RIJEKA = "20261126-SUPER,OSJEČKA 71 51000 RIJEKA,3271,113704,26.11.2026, 05-26.CSV"
RIVA = "20261126-MALI,RIVA 16 51000 RIJEKA,1527,113593,26.11.2026, 05-25.CSV"


def write_raw(data_dir, filename, content=None, day="2026-11-26"):
    path = data_dir / "raw" / "konzum" / day / (filename + ".gz")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8") if content is not None else SAMPLE.read_bytes()
    path.write_bytes(gzip.compress(data))
    return path


@pytest.fixture
def raw_file(tmp_path):
    return write_raw(tmp_path, RIJEKA)
