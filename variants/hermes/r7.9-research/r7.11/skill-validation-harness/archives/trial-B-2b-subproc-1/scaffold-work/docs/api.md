# API Documentation

## Export Endpoints

### Export Data
`GET /export/{format}`

Exports a list of records in the specified format.

**Path Parameters:**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `format` | `string` | The desired export format. Supported values: `csv`, `json`, `pdf`. |

**Query Parameters:**

The endpoint accepts a list of record objects via the `records` query parameter. 
*Note: In a production environment, this would typically be handled via a POST request or a database query, but for this implementation, it is passed as a list of dictionaries.*

**Response Types:**

| Format | Content-Type | Description |
| :--- | :--- | :--- |
| `csv` | `text/csv` | A string containing comma-separated values. |
| `json` | `application/json` | A JSON string representing the list of records. |
| `pdf` | `application/pdf` | Binary data representing the PDF document. |

**Error Responses:**

| Status Code | Detail | Reason |
| :--- | :--- | :--- |
| `400` | `Unsupported format` | The requested format is not supported. |
| `403` | `Permission denied for one or more records` | The user does not have ownership of one or more records in the list. |
