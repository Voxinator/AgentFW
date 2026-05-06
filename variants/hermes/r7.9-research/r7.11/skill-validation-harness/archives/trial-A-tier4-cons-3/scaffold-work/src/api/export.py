"""Export endpoints. Populated by capability-curve trials."""

from fastapi import APIRouter, HTTPException, Response, Depends

from src.auth import get_current_user, User
from src.auth.permissions import has_permission
from src.export.serializers import serialize

router = APIRouter(prefix="/api/export")


@router.get("/{format}")
async def export_records(
    format: str,
    user: User = Depends(get_current_user)
) -> Response:
    """
    Export records owned by the current user in the specified format.
    Supported formats: csv, json, pdf
    """
    # In a real app, these would come from a database. 
    # For the scaffold, we use a dummy set of records.
    # We include one record owned by the user and one not.
    dummy_records = [
        {"id": "rec1", "owner_id": "u1", "data": "user data 1"},
        {"id": "rec2", "owner_id": "u1", "data": "user data 2"},
        {"id": "rec3", "owner_id": "u2", "data": "other user data"},
    ]

    # Filter records based on ownership permission
    user_records = [r for r in dummy_records if has_permission(user, r)]

    if not user_records:
        raise HTTPException(status_code=404, detail="No records found for user")

    try:
        serialized_data = serialize(user_records, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Determine content type
    content_type_map = {
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf"
    }
    
    fmt_lower = format.lower()
    if fmt_lower not in content_type_map:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    content_type = content_type_map[fmt_lower]

    # Create response
    if isinstance(serialized_data, bytes):
        return Response(content=serialized_data, media_type=content_type)
    else:
        return Response(content=serialized_data, media_type=content_type)
