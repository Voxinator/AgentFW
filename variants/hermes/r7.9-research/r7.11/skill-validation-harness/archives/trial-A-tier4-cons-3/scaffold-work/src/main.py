from fastapi import FastAPI
from src.api.export import router as export_router

app = FastAPI()

app.include_router(export_router)

@app.get("/")
async def root():
    return {"message": "API is running"}
