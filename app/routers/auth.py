from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import COOKIE_NAME
from app.core.security import create_access_token
from app.schemas.auth import RegisterForm
from app.services.auth import AuthError, authenticate, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _login_response(user_id: int) -> RedirectResponse:
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user_id),
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.post("/register")
def register(
    email: str = Form(),
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    try:
        data = RegisterForm(email=email, username=username, password=password)
        user = register_user(db, data.email, data.username, data.password)
    except (ValidationError, AuthError) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return _login_response(user.id)


@router.post("/login")
def login(
    email: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    try:
        user = authenticate(db, email, password)
    except AuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return _login_response(user.id)


@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response
