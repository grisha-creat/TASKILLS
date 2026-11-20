from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User


class AuthError(Exception):
    pass


def register_user(db: Session, email: str, username: str, password: str) -> User:
    exists = db.scalar(
        select(User).where(or_(User.email == email, User.username == username))
    )
    if exists:
        raise AuthError("Пользователь с таким email или именем уже существует")
    user = User(email=email, username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Неверный email или пароль")
    return user
