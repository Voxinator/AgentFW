import json

def serialize_json(records: list[dict]) -> str:
    return json.dumps(records)
