from typing import Union, List, Dict
from .csv_exporter.csv import serialize_csv
from .json_exporter.json import serialize_json
from .pdf_exporter.pdf import serialize_pdf

def serialize_records(format_name: str, records: List[Dict]) -> Union[str, bytes]:
    """
    Unified interface for serializing records into different formats.
    
    Args:
        format_name: The desired format ('csv', 'json', 'pdf').
        records: A list of dictionaries containing the data.
        
    Returns:
        The serialized data as a string or bytes.
        
    Raises:
        ValueError: If the format_name is not supported.
    """
    if not records:
        if format_name == 'csv':
            return ""
        elif format_name == 'json':
            return "[]"
        elif format_name == 'pdf':
            return b""
        else:
            raise ValueError(f"Unsupported format: {format_name}")

    if format_name == 'csv':
        return serialize_csv(records)
    elif format_name == 'json':
        return serialize_json(records)
    elif format_name == 'pdf':
        return serialize_pdf(records)
    else:
        raise ValueError(f"Unsupported format: {format_name}")
