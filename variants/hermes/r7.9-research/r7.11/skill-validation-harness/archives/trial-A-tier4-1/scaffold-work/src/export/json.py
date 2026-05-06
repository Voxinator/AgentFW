import json

def serialize_json(records: list[dict]) -> str:
    if not records:
        return "[]"
    return json.dumps(records)
