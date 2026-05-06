# export-probe scaffold

Disposable scratch scaffold for r7.9 capability-curve trials. Wiped at session end.
All trial subtasks operate against `/tmp/export-probe-scaffold/`.

## API Endpoints

### Export Data
Returns data in requested format.

- `GET /api/export/csv?user_id=<user_id>&record_ids=<id1>&record_ids=<id2>`
  - Returns `text/csv`
- `GET /api/export/json?user_id=<user_id>&record_ids=<id1>&record_ids=<id2>`
  - Returns `application/json`
- `GET /api/export/pdf?user_id=<user_id>&record_ids=<id1>&record_ids=<id2>`
  - Returns `application/pdf`

#### Errors
- `400 Bad Request`: Unsupported format.
- `403 Forbidden`: Permission denied for one or more records.
