from typing import List, Dict, Any
from src.export import ExportFormat, get_serializer

def dummy_export_logic(format_str: str, data: List[Dict[str, Any]]):
    try:
        fmt = ExportFormat(format_str.lower())
    except ValueError:
        return None

    serializer = get_serializer(fmt)
    if not serializer:
        return None

    return serializer(data)

if __name__ == "__main__":
    # Test the wiring
    data = [{"id": 1, "name": "Test"}]
    assert dummy_export_logic("csv", data) is not None
    assert dummy_export_logic("json", data) is not None
    assert dummy_export_logic("pdf", data) is not None
    print("Wiring test passed!")
