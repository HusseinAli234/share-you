from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from app.core.settings import settings
from app.routers.auth import router as auth
from app.routers.projects import router as project
from app.utils.s3 import init_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_bucket()
    yield {}


app = FastAPI(lifespan=lifespan)


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
