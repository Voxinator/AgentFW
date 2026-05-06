from typing import List, Dict, Any, Optional
from .formats import ExportFormat
from .csv import serialize_csv
from .json import serialize_json
from .pdf import serialize_pdf

# Mapping for easy lookup
SERIALIZERS = {
    ExportFormat.CSV: serialize_csv,
    ExportFormat.JSON: serialize_json,
    ExportFormat.PDF: serialize_pdf,
}

def get_serializer(fmt: ExportFormat):
    """
    Returns the appropriate serializer function for the given ExportFormat.
    """
    return SERIALIZERS.get(fmt)

__all__ = ["ExportFormat", "serialize_csv", "serialize_json", "serialize_pdf", "SERIALIZERS", "get_serializer"]
