from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user_optional
from app.core.templates import templates
from app.models.models import Guide, User
from app.services.guides import (
    calc_progress,
    can_view,
    list_published,
    steps_with_state,
)

router = APIRouter(tags=["pages"])


@router.get("/")
def catalog(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    return templates.TemplateResponse(
        request,
        "catalog.html",
        {"current_user": current_user, "guides": list_published(db, q), "q": q},
    )


@router.get("/guides/{guide_id}")
def guide_page(
    guide_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    guide = db.get(Guide, guide_id)
    if guide is None or not can_view(guide, current_user):
        raise HTTPException(404, "Инструкция не найдена")
    steps = steps_with_state(db, guide.id, current_user)
    return templates.TemplateResponse(
        request,
        "guide.html",
        {
            "current_user": current_user,
            "guide": guide,
            "author": db.get(User, guide.author_id),
            "steps": steps,
            "progress": calc_progress(steps),
        },
    )


@router.get("/login")
def login_page(request: Request, current_user=Depends(get_current_user_optional)):
    return templates.TemplateResponse(request, "login.html", {"current_user": current_user})


@router.get("/register")
def register_page(request: Request, current_user=Depends(get_current_user_optional)):
    return templates.TemplateResponse(request, "register.html", {"current_user": current_user})
