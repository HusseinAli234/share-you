from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class RegisterForm(BaseModel):
    login: str
    password: str
    repeat_password: str

    @model_validator(mode="after")
    def verify_password_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Passwords do not match.")
        return self


class RegisterOut(BaseModel):
    message: str
    id: int


class LoginOut(BaseModel):
    token: str
    message: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    login: str
