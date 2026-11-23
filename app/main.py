from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.system import router as system_router
from app.routers.security import router as security_router
from app.routers.data import router as data_router

app = FastAPI(
    title="HAMSA AVIATOR AI",
    description="Research platform for Aviator statistics, dataset intelligence, and defensive cybersecurity analysis.",
    version="0.3.0",
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(system_router, prefix="/api/v1", tags=["system"])
app.include_router(security_router, prefix="/api/v1/security", tags=["security-research"])
app.include_router(data_router, prefix="/api/v1/data", tags=["data-intelligence"])

@app.get("/", tags=["system"])
async def root():
    return {
        "service": "HAMSA AVIATOR AI",
        "phase": "01B",
        "status": "running",
        "mode": "research",
        "data_source": "not_configured",
        "security_mode": "defensive_research",
    }
