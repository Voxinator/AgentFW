from enum import Enum
from typing import Protocol, Any

class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"

class Serializer(Protocol):
    def serialize(self, records: list[dict]) -> Any:
        ...

# Explicitly link the Serializer protocol to the functions for static analysis
def get_serializer(fmt: ExportFormat) -> Serializer:
    from .csv import serialize_csv
    from .json import serialize_json
    from .pdf import serialize_pdf
    
    mapping = {
        ExportFormat.CSV: type("CSVSerializer", (), {"serialize": staticmethod(serialize_csv)}),
        ExportFormat.JSON: type("JSONSerializer", (), {"serialize": staticmethod(serialize_json)}),
        ExportFormat.PDF: type("PDFSerializer", (), {"serialize": staticmethod(serialize_pdf)}),
    }
    return mapping[fmt]()
