import asyncio

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse, RedirectResponse

from app.db import Base, engine
from app.routers import auth, parts, web


app = FastAPI(title="AutoShop", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(parts.router)
app.include_router(web.router)

def _is_api(request: Request) -> bool:
    return request.url.path.startswith("/api")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # API keeps JSON errors.
    if _is_api(request):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    # Web UX:
    if exc.status_code == 401:
        # Token missing/expired -> send user to login and back.
        next_url = request.url.path
        if request.url.query:
            next_url = f"{next_url}?{request.url.query}"
        return RedirectResponse(url=f"/login?next={next_url}", status_code=303)

    if exc.status_code == 404:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": None,
                "title": "Страница не найдена",
                "message": "Похоже, такой страницы нет.",
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "user": None,
            "title": f"Ошибка {exc.status_code}",
            "message": str(exc.detail),
        },
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if _is_api(request):
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "user": None,
            "title": "Ошибка сервера",
            "message": "Что-то пошло не так. Попробуйте ещё раз или вернитесь на страницу входа.",
        },
        status_code=500,
    )


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

