from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hashed_password
from app.db.session import get_db
from app.models.users import User
from app.schemas.auth import RegisterForm, RegisterOut

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
