from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginOut, RegisterForm, RegisterOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterOut,
    summary="This endpoint for registration",
)
def register(form: RegisterForm, db: Session = Depends(get_db)):
    user = AuthService.register_user(db=db, form=form)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this login already exist!",
        )
    return {"message": "Succesefully created!", "id": user.id}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginOut,
    summary="This endpoint for login",
)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    token = AuthService.authenticate_user(
        db=db, username=form.username, password=form.password
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sign in"
        )

    return {"access_token": token, "message": "Successfully sign in"}


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserOut,
    summary="This endpoint for user information",
)
def get_user(user: User = Depends(get_current_user)):
    return user
