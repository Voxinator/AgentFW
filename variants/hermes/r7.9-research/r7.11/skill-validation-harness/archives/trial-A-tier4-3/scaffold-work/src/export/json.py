import json

def serialize_json(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a JSON string.
    
    Args:
        records: A list of dictionaries representing the data.
        
    Returns:
        A JSON formatted string. Returns an empty list string "[]" if records is empty.
    """
    return json.dumps(records)

def serialize_json_pretty(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a pretty-printed JSON string.
    
    Args:
        records: A list of dictionaries representing the data.
        
    Returns:
        A pretty-printed JSON formatted string.
    """
    return json.dumps(records, indent=4)

if __name__ == "__main__":
    # Test cases
    test_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    print("JSON Output:")
    print(serialize_json(test_data))
    
    print("\nPretty JSON Output:")
    print(serialize_json_pretty(test_data))
    
    print("\nEmpty Output:")
    print(f"'{serialize_json([])}'")
