from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import List
from src.auth import User, get_current_user
from src.auth.permissions import has_permission
from src.export.csv import export_to_csv
from src.export.json import export_to_json
from src.export.pdf import export_to_pdf

router = APIRouter(prefix="/api/export")

# Mock database of records
# In a real app, this would come from a database
MOCK_RECORDS = [
    {"id": "1", "owner_id": "u1", "data": "record 1 content"},
    {"id": "2", "owner_id": "u1", "data": "record 2 content"},
    {"id": "3", "owner_id": "u2", "data": "record 3 content"},
]

def get_user_records(user: User) -> List[dict]:
    """Helper to fetch records owned by the user."""
    return [r for r in MOCK_RECORDS if has_permission(user, r)]

def validate_record_access(user: User, record_id: str):
    """Validates that the user has permission to access the specific record."""
    record = next((r for r in MOCK_RECORDS if r["id"] == record_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if not has_permission(user, record):
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this record")
    return record

@router.get("/csv", response_class=Response)
async def export_csv(user: User = Depends(get_current_user)):
    """Export all records owned by the user to CSV."""
    records = get_user_records(user)
    content = export_to_csv(records)
    return Response(content=content, media_type="text/csv")

@router.get("/json", response_class=Response)
async def export_json(user: User = Depends(get_current_user)):
    """Export all records owned by the user to JSON."""
    records = get_user_records(user)
    content = export_to_json(records)
    return Response(content=content, media_type="application/json")

@router.get("/pdf", response_class=Response)
async def export_pdf(user: User = Depends(get_current_user)):
    """Export all records owned by the user to PDF."""
    records = get_user_records(user)
    content = export_to_pdf(records)
    return Response(content=content, media_type="application/pdf")

@router.get("/{record_id}/csv", response_class=Response)
async def export_single_csv(record_id: str, user: User = Depends(get_current_user)):
    """Export a single specific record to CSV."""
    record = validate_record_access(user, record_id)
    content = export_to_csv([record])
    return Response(content=content, media_type="text/csv")

@router.get("/{record_id}/json", response_class=Response)
async def export_single_json(record_id: str, user: User = Depends(get_current_user)):
    """Export a single specific record to JSON."""
    record = validate_record_access(user, record_id)
    content = export_to_json([record])
    return Response(content=content, media_type="application/json")

@router.get("/{record_id}/pdf", response_class=Response)
async def export_single_pdf(record_id: str, user: User = Depends(get_current_user)):
    """Export a single specific record to PDF."""
    record = validate_record_access(user, record_id)
    content = export_to_pdf([record])
    return Response(content=content, media_type="application/pdf")
