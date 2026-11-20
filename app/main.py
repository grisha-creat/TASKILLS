from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Step Guides")

from app.routers import auth

app.include_router(auth.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}
