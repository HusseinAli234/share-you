from fastapi import FastAPI

from app.routers.auth import router as auth

app = FastAPI()


app.include_router(auth)
