from fastapi import FastAPI, status

from app.routers.auth import router as auth
from app.routers.projects import router as project

app = FastAPI()


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
