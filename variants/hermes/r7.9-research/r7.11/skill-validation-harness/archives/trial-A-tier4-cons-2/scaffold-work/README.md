# export-probe scaffold

Disposable scratch scaffold for r7.9 capability-curve trials. Wiped at session end.
All trial subtasks operate against `/tmp/export-probe-scaffold/`.

## API Endpoints

### Export a Record
`GET /export/{record_id}?format={format}`

Exports a specific record in the requested format.

**Parameters:**
- `record_id` (path, string): The unique identifier of the record.
- `format` (query, string): The desired output format (`csv`, `json`, `pdf`).

**Returns:**
- `200 OK`: The exported content with appropriate `Content-Type`.
- `400 Bad Request`: Unsupported format or invalid parameters.
- `403 Forbidden`: User does not have permission to access the record.
- `404 Not Found`: Record not found.

### Export Batch
`GET /export/batch?format={format}`

Exports all records owned by the authenticated user.

**Parameters:**
- `format` (query, string): The desired output format (`csv`, `json`, `pdf`).

**Returns:**
- `200 OK`: The exported content (can be empty) with appropriate `Content-Type`.
- `400 Bad Request`: Unsupported format or invalid parameters.

## Running Tests

To run the test suite, use `pytest`:

```bash
pytest tests/
```
