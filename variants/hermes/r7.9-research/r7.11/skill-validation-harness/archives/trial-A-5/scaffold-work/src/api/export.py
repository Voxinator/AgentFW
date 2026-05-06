"""Export endpoints. Populated by capability-curve trials."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from src.auth import get_current_user, User
from src.auth.permissions import has_permission
from src.export.formats import serialize_csv, serialize_json, serialize_pdf

router = APIRouter()

# Mock data store for demonstration/testing
MOCK_RECORDS = [
    {"id": "1", "owner_id": "u1", "name": "Alice's Data 1", "value": 100},
    {"id": "2", "owner_id": "u1", "name": "Alice's Data 2", "value": 200},
    {"id": "3", "owner_id": "u2", "name": "Bob's Data 1", "value": 300},
]

@router.get("/export/{format_type}")
async def export_data(
    format_type: str,
    user: User = Depends(get_current_user)
) -> Response:
    """
    Export records owned by the current user in the specified format.
    Supported formats: csv, json, pdf
    """
    # 1. Filter data by ownership (Permissions check)
    user_records = filter_records_for_user(user, MOCK_RECORDS)
    
    if not user_records:
        raise HTTPException(status_code=404, detail="No records found for user")

    # 2. Serialize based on format
    if format_type == "csv":
        content = serialize_csv(user_records)
        media_type = "text/csv"
    elif format_type == "json":
        content = serialize_json(user_records)
        media_type = "application/json"
    elif format_type == "pdf":
        content = serialize_pdf(user_records)
        media_type = "application/pdf"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")

    # 3. Return response with correct media type
    # Note: serialize functions return str or bytes. Response handles both.
    return Response(content=content, media_type=media_type)
