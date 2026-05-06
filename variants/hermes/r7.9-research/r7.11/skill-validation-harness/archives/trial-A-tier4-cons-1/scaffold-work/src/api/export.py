from fastapi import APIRouter, HTTPException, Response, Depends
from typing import List
from src.auth import get_current_user, User
from src.auth.permissions import has_permission
from src.export.serializers import get_serializer

router = APIRouter()

# Mock data source for the purpose of this implementation
# In a real app, this would be a database query
MOCK_RECORDS = [
    {"id": "r1", "name": "Item 1", "owner_id": "u1", "data": "some data"},
    {"id": "r2", "name": "Item 2", "owner_id": "u1", "data": "other data"},
    {"id": "r3", "name": "Item 3", "owner_id": "u2", "data": "forbidden data"},
]

def get_records_for_user(user: User) -> List[dict]:
    """Filter records that the user has permission to access."""
    return [r for r in MOCK_RECORDS if has_permission(user, r)]

@router.get("/export/{format_name}")
async def export_records(
    format_name: str,
    user: User = Depends(get_current_user)
) -> Response:
    """
    Export all records owned by the current user in the specified format.
    Supported formats: csv, json, pdf
    """
    # 1. Validate format and get serializer
    try:
        serializer = get_serializer(format_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Get user's records (enforces ownership via has_permission)
    records = get_records_for_user(user)
    
    if not records:
        raise HTTPException(status_code=404, detail="No records found for user")

    # 3. Serialize data
    content = serializer(records)

    # 4. Determine media type
    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf", # Note: This is a simulated PDF in Phase 1
    }
    media_type = media_types.get(format_name.lower(), "application/octet-stream")

    return Response(content=content, media_type=media_type)

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from src.auth import get_current_user, User

    app = FastAPI()
    app.include_router(router)

    # Mock dependency for standalone execution
    TEST_USER = User(user_id="u1", email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: TEST_USER

    print("Starting export server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)

