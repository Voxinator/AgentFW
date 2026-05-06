import json
from typing import List, Dict, Union

def serialize_json(records: List[Dict]) -> str:
    """
    Serializes a list of dictionaries into a JSON string.
    """
    return json.dumps(records, indent=4)
