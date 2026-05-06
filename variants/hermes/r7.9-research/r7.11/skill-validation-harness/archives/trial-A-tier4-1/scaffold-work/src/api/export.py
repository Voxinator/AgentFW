from fastapi import APIRouter, Depends, HTTPException, Response
from src.auth import get_current_user, User
from src.auth.permissions import check_ownership
from src.export.formats import serialize_csv, serialize_json, serialize_pdf

router = APIRouter()

# Mock data source for the purpose of the exercise
# In a real app, this would be a DB query
MOCK_RECORDS = [
    {"id": "1", "owner_id": "u1", "data": "Alice's data"},
    {"id": "2", "owner_id": "u2", "data": "Bob's data"},
    {"id": "3", "owner_id": "u1", "data": "Alice's other data"},
]

def get_records_for_user(user_id: str):
    return [r for r in MOCK_RECORDS if r["owner_id"] == user_id]

def validate_ownership(user: User, record_id: str):
    record = next((r for r in MOCK_RECORDS if r["id"] == record_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if not check_ownership(user, record["owner_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to access this record")
    return record

@router.get("/export/csv/{record_id}")
async def export_csv(record_id: str, user: User = Depends(get_current_user)):
    record = validate_ownership(user, record_id)
    # For simplicity, we export the single record as a list of one dict
    data = serialize_csv([record])
    return Response(content=data, media_type="text/csv")

@router.get("/export/json/{record_id}")
async def export_json(record_id: str, user: User = Depends(get_current_user)):
    record = validate_ownership(user, record_id)
    data = serialize_json([record])
    return Response(content=data, media_type="application/json")

@router.get("/export/pdf/{record_id}")
async def export_pdf(record_id: str, user: User = Depends(get_current_user)):
    record = validate_ownership(user, record_id)
    data = serialize_pdf([record])
    return Response(content=data, media_type="application/pdf")
