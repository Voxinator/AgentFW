import json
from typing import List, Dict, Any

def serialize_json(data: List[Dict[str, Any]]) -> str:
    """
    Serializes a list of dictionaries to a JSON string.
    Handles empty lists by returning an empty JSON array.
    """
    return json.dumps(data, indent=2)
