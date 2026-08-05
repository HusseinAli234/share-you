from fastapi import (APIRouter, Depends, HTTPException,
                     OAuth2PasswordRequestForm, Request, status)
from sqlalchemy.orm import Session

from app.core.security import (create_access_token, get_current_user,
                               hashed_password, verify)
from app.db.session import get_db
from app.models.users import User
from app.schemas.auth import LoginOut, RegisterForm, RegisterOut

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterOut,
    summary="This endpoint for registration",
    tags=["Auth"],
)
def register(form: RegisterForm, db: Session = Depends(get_db)):
    has_user = db.query(User).filter(User.login == form.login).first()
    if has_user:
        raise HTTPException(
            status_code=403, detail="User with this login already exist!"
        )
    hashed = hashed_password(form.password)
    user = User(login=form.login, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Succesefully created!", "id": user.id}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginOut,
    summary="This endpoint for login",
    tags=["Auth"],
)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == form.username).first()
    if user and verify(form.password, user.hashed_password):
        token = create_access_token(user)
        return {"token": token, "message": "Successfully sign in"}
    else:
        raise HTTPException(status_code=403, detail="Invalid sign in")


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserOut,
    summary="This endpoint for user information",
    tags=["Auth"],
)
def get_user(user: User = Depends(get_current_user)):
    return user
