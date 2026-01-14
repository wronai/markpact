# FastAPI Todo API

REST API do zarządzania zadaniami z SQLite i pełnym CRUD.

## Uruchomienie

```bash
markpact examples/fastapi-todo/README.md
```

API będzie dostępne pod: http://localhost:8001

## Endpointy

- `GET /todos` – lista zadań
- `POST /todos` – utwórz zadanie
- `GET /todos/{id}` – szczegóły zadania
- `PUT /todos/{id}` – aktualizuj zadanie
- `DELETE /todos/{id}` – usuń zadanie

---

```markpact:deps python
fastapi
uvicorn
sqlalchemy
pydantic
```

```markpact:file python path=app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```markpact:file python path=app/models.py
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), default="")
    done = Column(Boolean, default=False)
```

```markpact:file python path=app/schemas.py
from pydantic import BaseModel

class TodoBase(BaseModel):
    title: str
    description: str = ""
    done: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(TodoBase):
    pass

class TodoResponse(TodoBase):
    id: int
    
    class Config:
        from_attributes = True
```

```markpact:file python path=app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import Todo
from app.schemas import TodoCreate, TodoUpdate, TodoResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo API", version="1.0.0")

@app.get("/todos", response_model=list[TodoResponse])
def list_todos(db: Session = Depends(get_db)):
    return db.query(Todo).all()

@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = Todo(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    for key, value in todo.model_dump().items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
```

```markpact:run python
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8001} --reload
```
