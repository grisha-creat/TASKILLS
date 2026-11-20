from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth

app = FastAPI(title="Step Guides")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}