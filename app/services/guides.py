from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Guide, Step, StepCompletion, User


def can_view(guide: Guide, user: User | None) -> bool:
    return guide.is_published or (user is not None and guide.author_id == user.id)


def list_published(db: Session, q: str = "") -> list[dict]:
    stmt = (
        select(Guide.id, Guide.title, Guide.description, User.username, func.count(Step.id))
        .join(User, User.id == Guide.author_id)
        .outerjoin(Step, Step.guide_id == Guide.id)
        .where(Guide.is_published.is_(True))
        .group_by(Guide.id, User.username)
        .order_by(Guide.created_at.desc())
    )
    q = q.strip()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Guide.title.ilike(like), Guide.description.ilike(like)))
    return [
        {
            "id": gid,
            "title": title,
            "description": description,
            "author_username": username,
            "steps_count": steps_count,
        }
        for gid, title, description, username, steps_count in db.execute(stmt)
    ]


def steps_with_state(db: Session, guide_id: int, user: User | None) -> list[dict]:
    steps = db.scalars(
        select(Step).where(Step.guide_id == guide_id).order_by(Step.position)
    ).all()
    done_ids: set[int] = set()
    if user is not None and steps:
        done_ids = set(
            db.scalars(
                select(StepCompletion.step_id).where(
                    StepCompletion.user_id == user.id,
                    StepCompletion.step_id.in_([s.id for s in steps]),
                )
            )
        )
    return [
        {
            "id": s.id,
            "position": s.position,
            "title": s.title,
            "body": s.body,
            "is_done": s.id in done_ids,
        }
        for s in steps
    ]


def calc_progress(steps: list[dict]) -> dict:
    total = len(steps)
    done = sum(1 for s in steps if s["is_done"])
    percent = round(done * 100 / total) if total else 0
    return {"done": done, "total": total, "percent": percent}


def set_completion(db: Session, user: User, step_id: int, done: bool) -> Step | None:
    """Отмечает или снимает шаг. Возвращает шаг или None, если он недоступен."""
    step = db.get(Step, step_id)
    if step is None:
        return None
    guide = db.get(Guide, step.guide_id)
    if guide is None or not can_view(guide, user):
        return None

    existing = db.scalar(
        select(StepCompletion).where(
            StepCompletion.user_id == user.id, StepCompletion.step_id == step_id
        )
    )
    try:
        if done and existing is None:
            db.add(StepCompletion(user_id=user.id, step_id=step_id))
            db.commit()
        elif not done and existing is not None:
            db.delete(existing)
            db.commit()
    except IntegrityError:
        db.rollback()  # двойной клик: отметка уже есть
    return step
