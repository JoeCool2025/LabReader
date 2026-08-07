from pathlib import Path

from txt_reader import tsv_reader


def test_tsv_reader_creates_database_file():
    sample_file = Path(__file__).with_name("Test_TSV.txt")
    tsv_reader(str(sample_file))

    db_path = Path(__file__).parent / "Databases" / "testdb.db"
    assert db_path.exists()
