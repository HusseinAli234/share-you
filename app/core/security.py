from passlib.context import CryptContext

secure_context = CryptContext(schemes=["argon2"])


def hashed_password(raw_password: str):
    hashed = secure_context.hash(raw_password)
    return hashed


def verify(raw_password: str, hashed_password: str) -> bool:
    return secure_context.verify(raw_password, hashed_password)
