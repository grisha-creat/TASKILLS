import os
import sys

sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.models import Guide, Step, User


def run_seed():
    db = SessionLocal()
    try:
        existing_users = db.execute(select(User)).scalars().all()
        if existing_users:
            print(f"Seed не нужен: уже есть {len(existing_users)} пользователей.")
            return

        # 1. Пользователи
        users = [
            User(email="anton@taskills.com", username="anton", password_hash="fake-hash-123"),
            User(email="grisha@taskills.com", username="grisha", password_hash="fake-hash-456"),
            User(email="test@taskills.com", username="tester", password_hash="fake-hash-789"),
        ]
        db.add_all(users)
        db.flush()

        # 2. Гайды
        guides = [
            Guide(
                author_id=users[0].id,
                title="Быстрый старт: как поднять бэкенд",
                description="Пошаговая инструкция по запуску проекта локально.",
                is_published=True,
            ),
            Guide(
                author_id=users[1].id,
                title="Работа с Git и PR",
                description="Как создавать ветки, коммитить и делать Pull Request.",
                is_published=True,
            ),
        ]
        db.add_all(guides)
        db.flush()

        # 3. Шаги первого гайда
        steps = [
            Step(guide_id=guides[0].id, position=1, title="Установка зависимостей",
                 body="Выполни pip install -r requirements.txt"),
            Step(guide_id=guides[0].id, position=2, title="Запуск Docker",
                 body="Запусти docker run для PostgreSQL (см. README)."),
            Step(guide_id=guides[0].id, position=3, title="Применение миграций",
                 body="Выполни alembic upgrade head"),
            Step(guide_id=guides[0].id, position=4, title="Проверка подключения",
                 body='Выполни python -c "from app.core.db import engine; print(engine.url)"'),
        ]
        db.add_all(steps)

        db.commit()
        print("Seed выполнен: 3 пользователя, 2 гайда, 4 шага.")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()