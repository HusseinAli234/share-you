import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status

from app.core.logger import logger, setup_logging
from app.routers.auth import router as auth
from app.routers.projects import router as project
from app.utils.s3 import init_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up application and initializing S3 bucket...")
    init_bucket()
    yield {}


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Completed in {process_time:.4f}s"
    )
    return response


app.include_router(auth)
app.include_router(project)


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Health check endpoint",
)
def health_check():
    return {"status": "ok"}
