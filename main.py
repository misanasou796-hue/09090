from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Cookie
from typing import Optional
import time
import secrets

from db_operations impopip install python 3.11rt (
    get_all_users, create_user_note, get_user_notes, delete_user_note,
    delete_all_user_notes, update_user_note, get_note_by_id, get_user_stats,
    authenticate_user, create_user, is_admin, get_admin_stats, get_all_notes_admin,
    get_user_activity, get_recent_activity
)
from models import UserRegister, UserLogin

app = FastAPI()

templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')

CSS_VERSION = str(int(time.time()))


def truncate_filter(s, length=100):
    if len(s) <= length:
        return s
    return s[:length] + '...'


templates.env.filters["truncate"] = truncate_filter
templates.env.globals["CSS_VERSION"] = CSS_VERSION

sessions = {}


def get_current_user(session_token: Optional[str] = Cookie(default=None)):
    if session_token and session_token in sessions:
        user_data = sessions[session_token]
        return user_data.get('email') if isinstance(user_data, dict) else user_data
    return None


def get_current_user_role(session_token: Optional[str] = Cookie(default=None)):
    if session_token and session_token in sessions:
        user_data = sessions[session_token]
        return user_data.get('role') if isinstance(user_data, dict) else 'user'
    return None


def create_session(user_email: str, user_role: str):
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = {
        'email': user_email,
        'role': user_role
    }
    return session_token


def delete_session(session_token: str):
    if session_token in sessions:
        del sessions[session_token]


@app.get('/home', response_class=HTMLResponse)
def home(request: Request,
         current_user: str = Depends(get_current_user),
         current_role: str = Depends(get_current_user_role)):
    if not current_user:
        return RedirectResponse(url='/authorization')

    user_notes = get_user_notes(current_user)

    user_activity = []
    if current_role == 'admin':
        user_activity = get_user_activity(current_user, 5)

    return templates.TemplateResponse(
        "index.html",
        {
            'request': request,
            'notes': user_notes,
            'current_user': current_user,
            'current_role': current_role,
            'user_activity': user_activity
        }
    )


@app.get('/admin', response_class=HTMLResponse)
def admin_panel(
        request: Request,
        current_user: str = Depends(get_current_user),
        current_role: str = Depends(get_current_user_role)
):
    if not current_user or current_role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    stats = get_admin_stats()
    all_users = get_all_users()
    recent_activity = get_recent_activity(20)
    all_notes = get_all_notes_admin()

    return templates.TemplateResponse(
        "admin.html",
        {
            'request': request,
            'stats': stats,
            'users': all_users,
            'recent_activity': recent_activity,
            'all_notes': all_notes,
            'current_user': current_user,
            'current_role': current_role
        }
    )


@app.post('/notes/create')
def create_note(
        title: str = Form(...),
        content: str = Form(...),
        current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    note_id = create_user_note(title, content, current_user)
    if note_id:
        return RedirectResponse(url='/home', status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Ошибка при создании заметки")


@app.post('/notes/deleteID')
def delete_note_id(
        note_id: int = Form(...),
        current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    if delete_user_note(note_id, current_user):
        return RedirectResponse(url='/home', status_code=303)
    else:
        raise HTTPException(status_code=404, detail='Заметка не найдена')


@app.post('/notes/{note_id}/delete')
def delete_note(
        note_id: int,
        current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    if delete_user_note(note_id, current_user):
        return RedirectResponse(url='/home', status_code=303)
    else:
        raise HTTPException(status_code=404, detail='Заметка не найдена')


@app.post('/notes/delete')
def delete_notes(current_user: str = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    if delete_all_user_notes(current_user):
        return RedirectResponse(url='/home', status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Ошибка при удалении заметок")


@app.post('/notes/update_ID')
def update_note_id(
        note_id: int = Form(...),
        title: str = Form(...),
        content: str = Form(...),
        current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    if update_user_note(note_id, title, content, current_user):
        return RedirectResponse(url='/home', status_code=303)
    else:
        raise HTTPException(status_code=404, detail='Заметка не найдена')


@app.post('/notes/{note_id}/update')
def update_note_route(
        note_id: int,
        title: str = Form(...),
        content: str = Form(...),
        current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    if update_user_note(note_id, title, content, current_user):
        return RedirectResponse(url='/home', status_code=303)
    else:
        raise HTTPException(status_code=404, detail='Заметка не найдена')


@app.get('/', response_class=HTMLResponse)
def register(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


@app.get('/authorization', response_class=HTMLResponse)
def authorization(request: Request):
    return templates.TemplateResponse('authorization.html', {'request': request})


@app.get('/logout')
def logout(request: Request, session_token: Optional[str] = Cookie(default=None)):
    response = RedirectResponse(url='/authorization')
    if session_token:
        delete_session(session_token)
        response.delete_cookie("session_token")
    return response


@app.get('/notes', response_class=HTMLResponse)
def get_notes(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url='/authorization')

    user_notes = get_user_notes(current_user)
    return templates.TemplateResponse('index2.html', {'request': request, 'notes': user_notes})


@app.get('/notes/{note_id}/update', response_class=HTMLResponse)
def update_note_form(note_id: int, request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url='/authorization')

    note = get_note_by_id(note_id, current_user)
    if note is None:
        raise HTTPException(status_code=404, detail='Заметка не найдена')

    return templates.TemplateResponse('index3.html', {'request': request, 'note': note})


@app.get('/notes/search', response_class=HTMLResponse)
def get_note(note_id: int, request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url='/authorization')

    note = get_note_by_id(note_id, current_user)
    if note:
        return templates.TemplateResponse('note.html', {'request': request, 'note': note})
    raise HTTPException(status_code=404, detail='Заметка не найдена')


@app.get('/notes/create', response_class=HTMLResponse)
def create_note_form(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url='/authorization')
    return templates.TemplateResponse('create_note.html', {'request': request})


@app.get('/notes/stats', response_class=HTMLResponse)
def get_len_notes(request: Request, current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url='/authorization')

    count = get_user_stats(current_user)
    return templates.TemplateResponse('len_notes.html', {'request': request, 'count': count})


@app.get('/users', response_class=HTMLResponse)
def get_users(
        request: Request,
        current_user: str = Depends(get_current_user),
        current_role: str = Depends(get_current_user_role)
):
    if not current_user:
        return RedirectResponse(url='/authorization')

    if current_role == 'admin':
        users = get_all_users()
    else:
        users = get_all_users()
        for user in users:
            user['last_login'] = None
            user['email'] = user['email'].split('@')[0] + '@***'

    return templates.TemplateResponse(
        'users.html',
        {
            'request': request,
            'users': users,
            'current_role': current_role
        }
    )


@app.post("/login/")
async def login_user(
        request: Request,
        email: str = Form(...),
        password: str = Form(...)
):
    client_host = request.client.host if request.client else None

    user_data = UserLogin(email=email, password=password)
    success, message, user_email, user_role = authenticate_user(user_data, client_host)

    if success:
        session_token = create_session(user_email, user_role)
        response = RedirectResponse(url="/home", status_code=303)
        response.set_cookie(key="session_token", value=session_token, httponly=True)
        return response
    else:
        return templates.TemplateResponse(
            'authorization.html',
            {
                'request': request,
                'error': message
            }
        )


@app.post("/register/")
async def register_user(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):
    user_data = UserRegister(name=name, email=email, password=password)
    success, message = create_user(user_data)

    if success:
        return RedirectResponse(url="/authorization", status_code=303)
    else:
        return templates.TemplateResponse(
            'register.html',
            {
                'request': request,
                'error': message
            }
        )


if __name__ == "__main__":
    import uvicorn

    print("🚀 Запуск сервера FastAPI...")
    print("📊 База данных: MySQL через HeidiSQL")
    print("🌐 Сайт доступен по адресу: http://127.0.0.1:8001")
    print("🔑 Администратор: admin@site.com / admin123")
    uvicorn.run(app, host="127.0.0.1", port=8001)