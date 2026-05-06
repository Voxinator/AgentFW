import csv
import io

def serialize_csv(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a CSV string.
    Returns an empty string if records is empty.
    """
    if not records:
        return ""

    output = io.StringIO()
    # Use keys from the first record as fieldnames
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(records)

    return output.getvalue()

if __name__ == "__main__":
    # Runtime call site to satisfy wiring check
    test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    print(serialize_csv(test_data))
