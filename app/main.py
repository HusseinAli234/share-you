from fastapi import FastAPI

from app.routers.auth import router as auth
from app.routers.projects import router as project
app = FastAPI()


app.include_router(auth)
app.include_router(project)
