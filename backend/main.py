import time

from fastapi import FastAPI, Request, Response

from backend.api.projects import router as projects_router
from backend.api.scans import router as scans_router
from backend.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    get_metrics,
)
from backend.services.persistence import initialize_database

app = FastAPI(
    title="SecureScan API",
    description="Security assessment platform for DevSecOps projects.",
    version="0.1.0",
)

initialize_database()

app.include_router(projects_router)
app.include_router(scans_router)


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        endpoint = getattr(route, "path", request.url.path)

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(time.perf_counter() - start_time)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "securescan-api",
        "version": "0.1.0",
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    content, content_type = get_metrics()
    return Response(
        content=content,
        headers={"Content-Type": content_type},
    )
