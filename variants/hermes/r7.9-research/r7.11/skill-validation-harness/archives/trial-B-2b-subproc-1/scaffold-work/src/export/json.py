import json

def serialize_json(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a JSON string.
    Handles empty list case by returning an empty list representation.
    """
    if not records:
        return "[]"
    
    return json.dumps(records, indent=4)
