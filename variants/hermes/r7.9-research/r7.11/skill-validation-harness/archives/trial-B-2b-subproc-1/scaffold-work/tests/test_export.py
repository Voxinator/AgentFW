import pytest
from fastapi import HTTPException
from src.api.export import export_data

from tests.fixtures import make_user, make_record

@pytest.mark.asyncio
async def test_export_csv_success():
    user = make_user("u1")
    records = [make_record("u1", 1), make_record("u1", 2)]
    # export_data returns the result of csv.serialize_csv(records)
    # In a real FastAPI app, we'd use TestClient, but here we call the function directly.
    # Note: export_data is async, so we await it.
    result = await export_data("csv", records, user)
    assert isinstance(result, str)
    assert "record-1" in result
    assert "record-2" in result

@pytest.mark.asyncio
async def test_export_json_success():
    user = make_user("u1")
    records = [make_record("u1", 1), make_record("u1", 2)]
    result = await export_data("json", records, user)
    assert isinstance(result, str)
    assert '"value": 1' in result
    assert '"value": 2' in result

@pytest.mark.asyncio
async def test_export_pdf_success():
    user = make_user("u1")
    records = [make_record("u1", 1)]
    result = await export_data("pdf", records, user)
    assert isinstance(result, bytes)

@pytest.mark.asyncio
async def test_export_permission_denied():
    user = make_user("u1")
    # One record belongs to u2
    records = [make_record("u1", 1), make_record("u2", 2)]
    with pytest.raises(HTTPException) as excinfo:
        await export_data("csv", records, user)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Permission denied for one or more records"

@pytest.mark.asyncio
async def test_export_unsupported_format():
    user = make_user("u1")
    records = [make_record("u1", 1)]
    with pytest.raises(HTTPException) as excinfo:
        await export_data("xml", records, user)
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Unsupported format"

@pytest.mark.asyncio
async def test_export_empty_records():
    user = make_user("u1")
    records = []
    # Testing CSV empty case
    result = await export_data("csv", records, user)
    assert isinstance(result, str)
    
    # Testing JSON empty case
    result = await export_data("json", records, user)
    assert result == "[]"
