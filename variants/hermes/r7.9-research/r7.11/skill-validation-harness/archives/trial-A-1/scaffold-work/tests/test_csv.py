from src.export.csv_exporter.csv import serialize_csv

def test_serialize_csv_with_data():
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    expected = "id,name\r\n1,Alice\r\n2,Bob\r\n"
    assert serialize_csv(data) == expected

def test_serialize_csv_empty():
    assert serialize_csv([]) == ""

def test_serialize_csv_single_record():
    data = [{"id": 1, "name": "Alice"}]
    expected = "id,name\r\n1,Alice\r\n"
    assert serialize_csv(data) == expected
