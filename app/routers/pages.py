from fastapi import APIRouter, Depends, Request

from app.core.deps import get_current_user_optional
from app.core.templates import templates

router = APIRouter(tags=["pages"])


@router.get("/")
def catalog(request: Request, q: str = "", current_user=Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request, "catalog.html", {"current_user": current_user, "guides": [], "q": q}
    )


@router.get("/login")
def login_page(request: Request, current_user=Depends(get_current_user_optional)):
    return templates.TemplateResponse(request, "login.html", {"current_user": current_user})


@router.get("/register")
def register_page(request: Request, current_user=Depends(get_current_user_optional)):
    return templates.TemplateResponse(request, "register.html", {"current_user": current_user})
