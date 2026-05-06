from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from src.auth.permissions import has_permission
from src.auth import User, get_current_user
from src.export import csv, json, pdf

router = APIRouter()

@router.get("/export/{format}")
async def export_data(format: str, records: List[Dict[str, Any]], user: User = Depends(get_current_user)):
    # 1. Permission Check
    for record in records:
        if not has_permission(user, record):
            raise HTTPException(status_code=403, detail="Permission denied for one or more records")

    # 2. Serialization
    if format == "csv":
        return csv.serialize_csv(records)
    elif format == "json":
        return json.serialize_json(records)
    elif format == "pdf":
        return pdf.serialize_pdf(records)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
