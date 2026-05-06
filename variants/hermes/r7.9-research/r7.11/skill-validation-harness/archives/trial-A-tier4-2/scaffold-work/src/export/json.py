import json

# Reference: serialize_json
def serialize_json(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries to a JSON string.
    Signature: (records: list[dict]) -> str
    """
    if not records:
        return "[]"

    return json.dumps(records)
