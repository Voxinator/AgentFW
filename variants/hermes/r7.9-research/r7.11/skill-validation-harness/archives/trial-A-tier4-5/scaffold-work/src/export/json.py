import json
from typing import List, Dict

def serialize_json(records: List[Dict]) -> str:
    if not records:
        return "[]"
    return json.dumps(records)
