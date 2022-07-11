from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

from fastapi import Depends, HTTPException, APIRouter, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from starlette.responses import RedirectResponse
from starlette import status

from database import SessionLocal, engine
import models

SECRET_KEY = 'broluja'
ALGORITHM = 'HS256'


class User(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str
    phone_number: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "username": "Username",
                "email": "email@email.com",
                "first_name": "FirstName",
                "last_name": "LastName",
                "password": "password",
                "phone_number": "064 2521241"
            }
        }


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
models.Base.metadata.create_all(bind=engine)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')
templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='/auth', tags=['auth'], responses={401: {'user': 'Not Authorized'}})


class LoginForm(object):
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('email')
        self.password = form.get('password')


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_password_hashed(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, email: str, user_id: int, expires_delta: Optional[timedelta] = None):
    sub = username + ' - ' + email
    encode = {"sub": sub, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request):
    try:
        token = request.cookies.get('access_token')
        if not token:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub').split(' - ')[0]
        user_id: str = payload.get('id')
        if username is None or user_id is None:
            logout(request)
        return {'Username': username, 'id': user_id}
    except JWTError:
        return HTTPException(status_code=404, detail='Not Found!')


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            msg = 'Incorrect Username or Password'
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = 'Unknown Error'
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.get('/logout')
async def logout(request: Request):
    msg = 'Logout Successful!'
    response = templates.TemplateResponse('login.html', {'request': request, 'msg': msg})
    response.delete_cookie(key='access_token')
    return response


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post('/register', response_class=HTMLResponse)
async def register_user(request: Request,
                        email: str = Form(...),
                        username: str = Form(...),
                        firstname: str = Form(...),
                        lastname: str = Form(...),
                        password: str = Form(...),
                        password2: str = Form(...),
                        db: Session = Depends(get_db)
                        ):
    validation1 = db.query(models.Users).filter(models.Users.username == username).first()
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()
    if password != password2 or validation1 is not None or validation2 is not None:
        msg = 'Invalid registration request!'
        return templates.TemplateResponse('register.html', {'request': request, 'msg': msg})

    user_model = models.Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname

    hash_password = get_password_hashed(password)
    user_model.hashed_password = hash_password
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg = 'User successfully created!'
    return templates.TemplateResponse('login.html', {'request': request, 'msg': msg})


@router.post("/token")
async def login_for_access_token(response: Response,
                                 form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return None
    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username, user.email, user.id, expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return user


# Exceptions

def get_user_exception():
    credentials_exceptions = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                           detail='Could not validate credentials',
                                           headers={'WWW-Authenticate': 'Bearer'})
    return credentials_exceptions


def token_exception():
    token_exception_response = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                             detail='Incorrect username or password',
                                             headers={'WWW-Authenticate': 'Bearer'})
    return token_exception_response
