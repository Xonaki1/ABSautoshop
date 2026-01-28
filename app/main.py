import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.routers import auth, parts, web


app = FastAPI(title="AutoShop", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(parts.router)
app.include_router(web.router)


@app.get("/health")
async def health():
    return {"ok": True}


async def _init_db_with_retry() -> None:
    last_err: Exception | None = None
    for _ in range(30):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except Exception as e:
            last_err = e
            await asyncio.sleep(1)
    raise last_err or RuntimeError("DB init failed")


@app.on_event("startup")
async def on_startup() -> None:
    await _init_db_with_retry()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await engine.dispose()

