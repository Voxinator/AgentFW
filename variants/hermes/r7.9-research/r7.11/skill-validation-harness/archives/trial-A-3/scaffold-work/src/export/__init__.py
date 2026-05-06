from typing import Dict, Callable, Any
from .formats import ExportFormat
from .csv import serialize_csv
from .json import serialize_json
from .pdf import serialize_pdf
from .smoke_test import run_smoke_test

SERIALIZERS: Dict[ExportFormat, Callable[[Any], Any]] = {
    ExportFormat.CSV: serialize_csv,
    ExportFormat.JSON: serialize_json,
    ExportFormat.PDF: serialize_pdf,
}

def get_serializer(fmt: ExportFormat) -> Callable[[Any], Any]:
    """
    Returns the serializer function for the given ExportFormat.
    """
    return SERIALIZERS[fmt]

__all__ = [
    "ExportFormat",
    "SERIALIZERS",
    "get_serializer",
    "serialize_csv",
    "serialize_json",
    "serialize_pdf",
    "run_smoke_test",
]
]
