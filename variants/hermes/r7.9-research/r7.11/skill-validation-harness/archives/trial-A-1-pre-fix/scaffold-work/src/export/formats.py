from typing import Any, Callable, Union

from .csv import serialize_csv
from .json import serialize_json
from .pdf import serialize_pdf

# Type alias for serializer functions
SerializerFunc = Callable[[list[dict[str, Any]]], Union[str, bytes]]

# Mapping of format names to their respective serializer functions
SERIALIZERS: dict[str, SerializerFunc] = {
    "csv": serialize_csv,
    "json": serialize_json,
    "pdf": serialize_pdf,
}

def get_serializer(format_name: str) -> SerializerFunc:
    """
    Retrieves the appropriate serializer function for the given format.
    
    Args:
        format_name: The name of the format (e.g., 'csv', 'json', 'pdf').
        
    Returns:
        The serializer function.
        
    Raises:
        ValueError: If the format is not supported.
    """
    serializer = SERIALIZERS.get(format_name.lower())
    if not serializer:
        supported = ", ".join(SERIALIZERS.keys())
        raise ValueError(f"Unsupported format: {format_name}. Supported formats: {supported}")
    return serializer
