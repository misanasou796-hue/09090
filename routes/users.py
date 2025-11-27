from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from schemas import UserRegister, UserLogin
from crud import create_user, authenticate_user, get_all_users

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/register/")
async def register_user(
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):
    """Регистрация нового пользователя"""
    user_data = UserRegister(name=name, email=email, password=password)
    success, message = create_user(user_data)

    if success:
        return RedirectResponse(url="/authorization", status_code=303)
    else:
        raise HTTPException(status_code=400, detail=message)


@router.post("/login/")
async def login_user(
        email: str = Form(...),
        password: str = Form(...)
):
    """Аутентификация пользователя"""
    user_data = UserLogin(email=email, password=password)
    success, message = authenticate_user(user_data)

    if success:
        return RedirectResponse(url="/home", status_code=303)
    else:
        raise HTTPException(status_code=400, detail=message)


@router.get("/api/users")
async def get_users_api():
    """API для получения списка пользователей"""
    users = get_all_users()
    return {"users": [{"name": user.name, "email": user.email} for user in users]}
