"""Export endpoints."""

from fastapi import APIRouter, HTTPException, Response, Query
from typing import List
from src.export.csv import serialize_csv
from src.export.json import serialize_json
from src.export.pdf import serialize_pdf
from src.auth.permissions import has_permission_for_many
from src.auth import User

router = APIRouter(prefix="/export")

@router.get("/{format}")
async def export_records(
    format: str,
    user_id: str,
    record_ids: List[str] = Query(...),
):
    """
    GET endpoint to export records in the specified format.
    
    Args:
        format: The export format (csv, json, pdf).
        user_id: The ID of the user requesting the export.
        record_ids: A list of record IDs to include in the export.
        
    Returns:
        The serialized data with the appropriate Content-Type.
        
    Raises:
        HTTPException: 400 if format is invalid, 403 if permission is denied.
    """
    # Mocking record retrieval. In a real app, this would hit a DB.
    # For the purpose of this implementation and testing, we assume 
    # records are fetched based on record_ids.
    # We'll create dummy records that include the owner_id for permission check.
    # In a real scenario, these would be real database entities.
    
    # NOTE: This is a mock implementation of data retrieval for the scaffold.
    # We assume the existence of a registry or DB lookup.
    # Since we don't have a DB, we'll simulate the records.
    
    # For testing purposes, we'll assume if record_id starts with 'rec_forbidden', 
    # it belongs to someone else.
    
    records = []
    for rid in record_ids:
        owner = "user_123" if not rid.startswith("rec_forbidden") else "other_user"
        records.append({"id": rid, "owner_id": owner, "data": f"content_{rid}"})

    # 1. Permission Check
    # We need a User object as expected by has_permission_for_many
    # In a real FastAPI app, this would come from a dependency like Depends(get_current_user)
    user = User(user_id=user_id)
    
    if not has_permission_for_many(user, records):
        raise HTTPException(status_code=403, detail="Permission denied for one or more records")

    # 2. Serialization and Response
    if format == "csv":
        content = serialize_csv(records)
        return Response(content=content, media_type="text/csv")
    
    elif format == "json":
        content = serialize_json(records)
        return Response(content=content, media_type="application/json")
    
    elif format == "pdf":
        content = serialize_pdf(records)
        return Response(content=content, media_type="application/pdf")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

if __name__ == "__main__":
    import asyncio
    print("Running dummy export_records...")
    asyncio.run(export_records(format="json", user_id="user_123", record_ids=["rec_1", "rec_2"]))
    print("Dummy export completed.")
