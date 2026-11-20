from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user_optional
from app.core.templates import templates
from app.models.models import Guide
from app.services.guides import (
    guide_analytics,
    list_by_author,
    save_guide,
    steps_with_state,
)

router = APIRouter(tags=["cabinet"])


def _to_login():
    return RedirectResponse("/login", status_code=303)


def _build_items(step_id: list[str], step_title: list[str], step_body: list[str]):
    items = []
    for i, title in enumerate(step_title):
        title = title.strip()
        if not title:
            continue
        raw_id = step_id[i] if i < len(step_id) else ""
        items.append({
            "id": int(raw_id) if raw_id.isdigit() else None,
            "title": title,
            "body": step_body[i].strip() if i < len(step_body) else "",
        })
    return items


def _own_guide(db: Session, guide_id: int, user) -> Guide:
    guide = db.get(Guide, guide_id)
    if guide is None or guide.author_id != user.id:
        raise HTTPException(404, "Инструкция не найдена")
    return guide


def _form(request, user, guide, steps, error=None, status_code=200):
    return templates.TemplateResponse(
        request,
        "guide_form.html",
        {"current_user": user, "guide": guide, "steps": steps, "error": error},
        status_code=status_code,
    )


@router.get("/my")
def my_guides(request: Request, db: Session = Depends(get_db),
              user=Depends(get_current_user_optional)):
    if user is None:
        return _to_login()
    return templates.TemplateResponse(
        request, "my_guides.html",
        {"current_user": user, "guides": list_by_author(db, user.id)},
    )


@router.get("/guides/new")
def new_form(request: Request, user=Depends(get_current_user_optional)):
    if user is None:
        return _to_login()
    return _form(request, user, None, [])


@router.post("/guides")
def create(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    is_published: str | None = Form(None),
    step_id: list[str] = Form([]),
    step_title: list[str] = Form([]),
    step_body: list[str] = Form([]),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    if user is None:
        return _to_login()
    items = _build_items(step_id, step_title, step_body)
    if not title.strip() or not items:
        draft = {"id": None, "title": title, "description": description,
                 "is_published": bool(is_published)}
        return _form(request, user, draft, items,
                     "Укажите название и добавьте хотя бы один шаг с заголовком", 400)
    save_guide(db, user, None, title.strip(), description.strip(),
               bool(is_published), items)
    return RedirectResponse("/my", status_code=303)


@router.get("/guides/{guide_id}/edit")
def edit_form(guide_id: int, request: Request, db: Session = Depends(get_db),
              user=Depends(get_current_user_optional)):
    if user is None:
        return _to_login()
    guide = _own_guide(db, guide_id, user)
    return _form(request, user, guide, steps_with_state(db, guide.id, None))


@router.post("/guides/{guide_id}")
def update(
    guide_id: int,
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    is_published: str | None = Form(None),
    step_id: list[str] = Form([]),
    step_title: list[str] = Form([]),
    step_body: list[str] = Form([]),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    if user is None:
        return _to_login()
    guide = _own_guide(db, guide_id, user)
    items = _build_items(step_id, step_title, step_body)
    if not title.strip() or not items:
        draft = {"id": guide.id, "title": title, "description": description,
                 "is_published": bool(is_published)}
        return _form(request, user, draft, items,
                     "Укажите название и добавьте хотя бы один шаг с заголовком", 400)
    save_guide(db, user, guide, title.strip(), description.strip(),
               bool(is_published), items)
    return RedirectResponse("/my", status_code=303)


@router.get("/guides/{guide_id}/analytics")
def analytics(guide_id: int, request: Request, db: Session = Depends(get_db),
              user=Depends(get_current_user_optional)):
    if user is None:
        return _to_login()
    guide = _own_guide(db, guide_id, user)
    return templates.TemplateResponse(
        request, "analytics.html",
        {"current_user": user, "guide": guide, "stats": guide_analytics(db, guide.id)},
    )
