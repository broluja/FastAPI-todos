from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from starlette import status
from starlette.responses import RedirectResponse

import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from .auth import get_current_user

router = APIRouter(prefix='/todos', tags=['todos'], responses={404: {'description': 'Not found'}})
models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory='templates')


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class ToDo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, lt=6, description='The priority must be between 1-5')
    complete: bool

    class Config:
        schema_extra = {
            "example": {
                "title": "What`s your ToDO",
                "description": "Short description",
                "priority": 1,
                "complete": "false"}
        }


@router.get('/', response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    todos = db.query(models.ToDos).filter(models.ToDos.owner_id == user.get('id')).all()
    print(todos)
    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, 'user': user})


@router.get('/add-todo', response_class=HTMLResponse)
async def add_new_todo(request: Request):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request": request, 'user': user})


@router.post('/add-todo', response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...),
                      description: str = Form(...),
                      priority: str = Form(...),
                      db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    todo_model = models.ToDos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get('id')

    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    todo = db.query(models.ToDos).filter(models.ToDos.id == todo_id).first()
    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, 'user': user})


@router.post('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo_commit(request: Request,
                           todo_id: int,
                           title: str = Form(...),
                           description: str = Form(...),
                           priority: int = Form(...),
                           db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.ToDos).filter(models.ToDos.id == todo_id).first()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.ToDos).filter(models.ToDos.id == todo_id).filter(
        models.ToDos.owner_id == user.get('id')).first()
    if not todo_model:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.ToDos).filter(models.ToDos.id == todo_id).delete()
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}")
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    todo = db.query(models.ToDos).filter(models.ToDos.id == todo_id).first()
    todo.complete = not todo.complete

    db.add(todo)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
