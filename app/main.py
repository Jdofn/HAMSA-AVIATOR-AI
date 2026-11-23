from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.system import router as system_router

app = FastAPI(
    title="HAMSA AVIATOR AI",
    description="Research platform foundation for statistical analysis of Aviator rounds.",
    version="0.1.0",
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(system_router, prefix="/api/v1", tags=["system"])

@app.get("/", tags=["system"])
async def root():
    return {
        "service": "HAMSA AVIATOR AI",
        "phase": "01",
        "status": "running",
        "mode": "research",
        "data_source": "not_configured",
    }
