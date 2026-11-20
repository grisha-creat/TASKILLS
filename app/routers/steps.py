from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.templates import templates
from app.models.models import User
from app.services.guides import calc_progress, set_completion, steps_with_state

router = APIRouter(tags=["steps"])


def _toggle(request: Request, step_id: int, done: bool, db: Session, user: User):
    step = set_completion(db, user, step_id, done)
    if step is None:
        raise HTTPException(404, "Шаг не найден")
    steps = steps_with_state(db, step.guide_id, user)
    return templates.TemplateResponse(
        request,
        "_steps.html",
        {"current_user": user, "steps": steps, "progress": calc_progress(steps)},
    )


@router.post("/steps/{step_id}/complete")
def complete(
    step_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _toggle(request, step_id, True, db, user)


@router.delete("/steps/{step_id}/complete")
def uncomplete(
    step_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _toggle(request, step_id, False, db, user)
