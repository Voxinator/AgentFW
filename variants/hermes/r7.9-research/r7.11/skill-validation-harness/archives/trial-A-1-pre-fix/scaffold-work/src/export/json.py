import json

def serialize_json(data: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a JSON string.
    
    Args:
        data: A list of dictionaries to serialize.
        
    Returns:
        A JSON formatted string.
    """
    return json.dumps(data, indent=2)
