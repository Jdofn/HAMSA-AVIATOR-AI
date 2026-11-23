from fastapi import APIRouter
from sqlalchemy import text
from app.db import engine

router = APIRouter()

@router.get("")
async def health():
    return {"status": "ok", "service": "api"}

@router.get("/database")
async def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}
