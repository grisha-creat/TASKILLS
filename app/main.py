from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth, my, pages, steps

app = FastAPI(title="Step Guides")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth.router)
app.include_router(my.router)
app.include_router(pages.router)
app.include_router(steps.router)


@app.get("/health")
def health():
    return {"status": "ok"}
