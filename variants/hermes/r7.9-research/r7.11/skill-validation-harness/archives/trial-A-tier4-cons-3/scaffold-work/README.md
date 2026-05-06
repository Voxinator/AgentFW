# Export Feature

This project provides an API for exporting user records in various formats.

## API Endpoints

### Export Records
`GET /api/export/{format}`

Exports records owned by the authenticated user.

**Supported Formats:**
- `csv`: Returns `text/csv` content.
- `json`: Returns `application/json` content.
- `pdf`: Returns `application/pdf` content.

**Errors:**
- `400 Bad Request`: Unsupported format or serialization error.
- `404 Not Found`: No records found for the user.
- `401 Unauthorized`: Missing or invalid authentication.

## Running Tests

To run the test suite, use:
```bash
.venv/bin/pytest tests/
```
