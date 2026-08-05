

from fastapi import FastAPI

from app.router.auth import router as auth
app = FastAPI()


app.include_router(auth)




