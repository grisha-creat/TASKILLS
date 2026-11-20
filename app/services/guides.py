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


def guide_analytics(db: Session, guide_id: int) -> dict:
    steps = db.scalars(
        select(Step).where(Step.guide_id == guide_id).order_by(Step.position)
    ).all()

    base = (
        select(StepCompletion)
        .join(Step, Step.id == StepCompletion.step_id)
        .where(Step.guide_id == guide_id)
    )
    started = db.scalar(
        select(func.count(func.distinct(StepCompletion.user_id)))
        .join(Step, Step.id == StepCompletion.step_id)
        .where(Step.guide_id == guide_id)
    ) or 0

    counts = dict(
        db.execute(
            select(StepCompletion.step_id, func.count(func.distinct(StepCompletion.user_id)))
            .join(Step, Step.id == StepCompletion.step_id)
            .where(Step.guide_id == guide_id)
            .group_by(StepCompletion.step_id)
        ).all()
    )

    finished = 0
    if steps:
        per_user = (
            select(StepCompletion.user_id)
            .join(Step, Step.id == StepCompletion.step_id)
            .where(Step.guide_id == guide_id)
            .group_by(StepCompletion.user_id)
            .having(func.count(func.distinct(StepCompletion.step_id)) == len(steps))
            .subquery()
        )
        finished = db.scalar(select(func.count()).select_from(per_user)) or 0

    rows = []
    prev = started
    for s in steps:
        c = counts.get(s.id, 0)
        rows.append({
            "position": s.position,
            "title": s.title,
            "completed_count": c,
            "percent": round(c * 100 / started) if started else 0,
            "drop": max(prev - c, 0),
            "is_bottleneck": False,
        })
        prev = c

    with_drop = [r for r in rows if r["drop"] > 0]
    if with_drop:
        max(with_drop, key=lambda r: r["drop"])["is_bottleneck"] = True

    return {
        "started": started,
        "finished": finished,
        "finish_percent": round(finished * 100 / started) if started else 0,
        "rows": rows,
    }


def list_by_author(db: Session, author_id: int) -> list[dict]:
    stmt = (
        select(Guide.id, Guide.title, Guide.is_published, func.count(Step.id))
        .outerjoin(Step, Step.guide_id == Guide.id)
        .where(Guide.author_id == author_id)
        .group_by(Guide.id)
        .order_by(Guide.created_at.desc())
    )
    return [
        {"id": gid, "title": title, "is_published": pub, "steps_count": cnt}
        for gid, title, pub, cnt in db.execute(stmt)
    ]


def save_guide(
    db: Session,
    user: User,
    guide: Guide | None,
    title: str,
    description: str,
    is_published: bool,
    items: list[dict],
) -> Guide:
    """Создаёт или обновляет инструкцию вместе с шагами.

    items: [{"id": int | None, "title": str, "body": str}] в нужном порядке.
    Шаги с известным id обновляются (отметки пользователей сохраняются),
    новые создаются, пропавшие из списка удаляются.
    """
    if guide is None:
        guide = Guide(author_id=user.id, title=title, description=description,
                      is_published=is_published)
        db.add(guide)
        db.flush()
    else:
        guide.title = title
        guide.description = description
        guide.is_published = is_published

    existing = {
        s.id: s for s in db.scalars(select(Step).where(Step.guide_id == guide.id))
    }
    keep = {i["id"] for i in items if i["id"] in existing}

    for sid, step in list(existing.items()):
        if sid not in keep:
            db.delete(step)
            del existing[sid]
    db.flush()

    # временный сдвиг, чтобы не нарушить unique(guide_id, position)
    for step in existing.values():
        step.position += 100000
    db.flush()

    for pos, item in enumerate(items, start=1):
        if item["id"] in keep:
            step = existing[item["id"]]
            step.title, step.body, step.position = item["title"], item["body"], pos
        else:
            db.add(Step(guide_id=guide.id, position=pos,
                        title=item["title"], body=item["body"]))
    db.commit()
    db.refresh(guide)
    return guide
