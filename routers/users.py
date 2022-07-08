from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine

from .auth import get_current_user, get_password_hashed, verify_password
import models

router = APIRouter(prefix='/users', tags=['users'], responses={404: {'description': 'Not Found'}})
models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory='templates')


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get('/edit-password', response_class=HTMLResponse)
async def user_password_change(request: Request):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse('change-password.html', {'request': request, 'user': user})


@router.post('/edit-password', response_class=HTMLResponse)
async def user_password_change(request: Request,
                               username: str = Form(...),
                               password: str = Form(...),
                               password2: str = Form(...),
                               db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    user_data = db.query(models.Users).filter(models.Users.username == username).first()
    msg = 'Invalid username or password'
    if user_data is not None:
        if username == user_data.username and verify_password(password, user_data.hashed_password):
            user_data.hashed_password = get_password_hashed(password2)
            db.add(user_data)
            db.commit()
            msg = 'Password updated'
    return templates.TemplateResponse('change-password.html', {'request': request, 'user': user, 'msg':msg})
