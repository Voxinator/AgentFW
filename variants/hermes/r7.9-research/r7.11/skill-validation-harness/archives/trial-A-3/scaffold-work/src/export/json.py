import json
from typing import List, Dict, Any

def serialize_json(records: List[Dict[str, Any]]) -> str:
    """
    Serializes a list of dictionaries to a JSON string.
    """
    return json.dumps(records, indent=2)
