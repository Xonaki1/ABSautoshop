from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.security import create_access_token
from app.supplier import SupplierClient
from app.users import authenticate_user, create_user, get_user_by_username

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["web"])


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _redirect("/search")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"}, status_code=400)
    token = create_access_token(subject=user.username)
    resp = _redirect("/search")
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
async def register_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    existing = await get_user_by_username(db, username)
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Такой логин уже занят"}, status_code=400)
    user = await create_user(db, username, password)
    token = create_access_token(subject=user.username)
    resp = _redirect("/search")
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp


@router.post("/logout")
async def logout_action():
    resp = _redirect("/login")
    resp.delete_cookie("access_token")
    return resp


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("search.html", {"request": request, "user": user, "offers": None, "number": "", "error": None})


@router.post("/search", response_class=HTMLResponse)
async def search_action(
    request: Request,
    number: str = Form(...),
    user=Depends(get_current_user),
):
    client = SupplierClient()
    try:
        offers = await client.search(number)
        error = None
    except (httpx.HTTPError, RuntimeError) as e:
        offers = []
        error = str(e)
    finally:
        await client.aclose()
    return templates.TemplateResponse(
        "search.html",
        {"request": request, "user": user, "offers": offers, "number": number.strip().upper(), "error": error},
    )

