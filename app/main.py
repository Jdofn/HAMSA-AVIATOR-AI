from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.system import router as system_router
from app.routers.security import router as security_router
from app.routers.data import router as data_router
from app.routers.lab import router as lab_router
from app.aviator_import import router as aviator_import_router
from app.aviator_analytics import router as aviator_analytics_router
from app.aviator_dashboard import router as aviator_dashboard_router

app = FastAPI(
    title="HAMSA AVIATOR AI",
    description="Aviator research platform with offline imports, historical analytics, and authorized defensive protocol analysis.",
    version="0.6.0",
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(system_router, prefix="/api/v1", tags=["system"])
app.include_router(security_router, prefix="/api/v1/security", tags=["security-research"])
app.include_router(data_router, prefix="/api/v1/data", tags=["data-intelligence"])
app.include_router(aviator_import_router, prefix="/api/v1/data", tags=["aviator-import"])
app.include_router(aviator_analytics_router, prefix="/api/v1/aviator", tags=["aviator-analytics"])
app.include_router(aviator_dashboard_router, tags=["aviator-dashboard"])
app.include_router(lab_router, prefix="/api/v1/lab", tags=["authorized-lab"])


@app.get("/", tags=["system"])
async def root():
    return {
        "service": "HAMSA AVIATOR AI",
        "phase": "02",
        "status": "running",
        "mode": "research",
        "data_source": "user_supplied_exports_only",
        "security_mode": "defensive_research",
    }
