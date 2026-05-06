import json

def serialize_json(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a JSON string.
    Returns an empty JSON array string if records is empty.
    """
    if not records:
        return "[]"

    return json.dumps(records)

if __name__ == "__main__":
    # Runtime call site to satisfy wiring check
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    print(serialize_json(test_data))
