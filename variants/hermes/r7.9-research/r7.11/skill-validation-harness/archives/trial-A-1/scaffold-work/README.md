# Export Feature

This module provides capabilities to export data in various formats (CSV, JSON, PDF) with built-in permission checks.

## API Documentation

### `export_data`

Exports a list of records if the user has permission for all records.

**Signature:**
`export_data(user: User, records: List[Dict[str, Any]], format: str) -> Union[str, bytes]`

**Arguments:**
- `user`: The `User` object attempting the export.
- `records`: A list of dictionaries representing the data to be exported.
- `format`: The desired export format. Supported values: `'csv'`, `'json'`, `'pdf'`.

**Returns:**
- The serialized data in the requested format. 
- For `'csv'` and `'json'`, returns a `str`.
- For `'pdf'`, returns `bytes`.

**Raises:**
- `PermissionError`: If the user does not have permission for one or more records in the list.
- `ValueError`: If an unsupported format is requested.

## Formats Supported

| Format | Return Type | Description |
|--------|------------|-------------|
| CSV    | `str`      | Comma-separated values. |
| JSON   | `str`      | JSON array of objects. |
| PDF    | `bytes`    | A PDF document containing a table of the data. |

## Installation

Ensure you have the required dependencies installed:

```bash
pip install reportlab pytest
```
