from fastapi import FastAPI

from backend.api.projects import router as projects_router
from backend.api.scans import router as scans_router
from backend.services.persistence import initialize_database

app = FastAPI(
    title="SecureScan API",
    description="Security assessment platform for DevSecOps projects.",
    version="0.1.0",
)

initialize_database()

app.include_router(projects_router)
app.include_router(scans_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "securescan-api",
        "version": "0.1.0",
    }
