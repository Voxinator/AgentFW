from fastapi import APIRouter, Depends, HTTPException, Response
from src.auth import User, get_current_user
from src.auth.permissions import has_permission
from src.export import serialize
import asyncio

router = APIRouter()

@router.get("/export/{record_id}")
async def export_record(
    record_id: str, 
    format: str, 
    user: User = Depends(get_current_user)
):
    """
    Export a specific record by ID in the requested format.
    Note: For this scaffold, we simulate fetching a record.
    """
    # Mock database lookup
    # In a real app, this would query a database
    mock_db = {
        "r1": {"id": "r1", "owner_id": "u1", "data": "record 1 content"},
        "r2": {"id": "r2", "owner_id": "u2", "data": "record 2 content"},
    }

    record = mock_db.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Check permissions
    if not has_permission(user, record):
        raise HTTPException(status_code=403, detail="Not authorized to access this record")

    # Perform serialization
    try:
        content = serialize(format, [record])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Determine media type
    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf"
    }
    
    media_type = media_types.get(format.lower())
    if not media_type:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    if format.lower() == "csv":
        media_type = "text/csv"


    # Prepare response
    if isinstance(content, bytes):
        return Response(content=content, media_type=media_type)
    else:
        return Response(content=content, media_type=media_type)

@router.get("/export/batch")
async def export_batch(
    format: str, 
    user: User = Depends(get_current_user)
):
    """
    Export all records owned by the user.
    """
    # Mock database lookup of all records
    mock_db = [
        {"id": "r1", "owner_id": "u1", "data": "record 1 content"},
        {"id": "r2", "owner_id": "u2", "data": "record 2 content"},
        {"id": "r3", "owner_id": "u1", "data": "record 3 content"},
    ]

    # Filter records by ownership
    user_records = [r for r in mock_db if has_permission(user, r)]

    try:
        content = serialize(format, user_records)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf"
    }
    
    media_type = media_types.get(format.lower())
    if not media_type:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return Response(content=content, media_type=media_type)


if __name__ == "__main__":
    async def main():
        user = get_current_user()
        print("Testing export_record:")
        try:
            res1 = await export_record("r1", "json", user)
            print(f"r1 json: {res1.body.decode()}")
        except Exception as e:
            print(f"r1 error: {e}")

        try:
            res2 = await export_record("r2", "csv", user)
            print(f"r2 csv: {res2.body.decode()}")
        except Exception as e:
            print(f"r2 error: {e}")

        print("\nTesting export_batch:")
        try:
            res3 = await export_batch("json", user)
            print(f"batch json: {res3.body.decode()}")
        except Exception as e:
            print(f"batch error: {e}")

    asyncio.run(main())
