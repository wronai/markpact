# URL Shortener

A minimal, production‑ready URL shortener built with **FastAPI**, **SQLite**, and **SQLAlchemy**.  
It supports custom aliases, automatic code generation, active/inactive flagging, and a clean JSON API.

## Features
- Create short URLs with optional custom aliases
- Automatic incremental short‑code generation
- Redirects to the original URL with a 302 response
- List all active short URLs via a JSON endpoint
- Deactivate (soft‑delete) short URLs
- CORS enabled for easy front‑end integration
- SQLite database for zero‑config deployment

## API Endpoints
- **POST** `/shorten` – Create a new short URL  
- **GET** `/{short_code}` – Redirect to the original URL  
- **GET** `/api/urls` – List all active short URLs  
- **DELETE** `/{short_code}` – Deactivate a short URL  

---

```markpact:deps python
fastapi
uvicorn
sqlalchemy
pydantic
```

```markpact:file python path=app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field
from typing import List, Optional
import os

# ----------------------------------------------------------------------
# Database Setup
# ----------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shorteners.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ShortURL(Base):
    __tablename__ = "short_urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)


Base.metadata.create_all(bind=engine)


# ----------------------------------------------------------------------
# Pydantic Models
# ----------------------------------------------------------------------
class ShortURLCreate(BaseModel):
    original_url: str = Field(..., example="https://example.com")
    custom_alias: Optional[str] = Field(None, example="ex")

    class Config:
        json_schema_extra = {
            "example": {"original_url": "https://example.com", "custom_alias": "ex"}
        }


class ShortURLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    is_active: bool

    class Config:
        orm_mode = True


# ----------------------------------------------------------------------
# FastAPI App
# ----------------------------------------------------------------------
app = FastAPI()

# Enable CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------
@app.post("/shorten", response_model=ShortURLResponse)
async def create_short_url(payload: ShortURLCreate, db: SessionLocal = Depends(get_db)):
    # Resolve custom alias or generate one
    if payload.custom_alias:
        if db.query(ShortURL).filter(ShortURL.short_code == payload.custom_alias).first():
            raise HTTPException(status_code=400, detail="Custom alias already in use")
        short_code = payload.custom_alias
    else:
        # Simple incremental code generation
        last = db.query(ShortURL).order_by(ShortURL.id.desc()).first()
        short_code = str(last.id + 1) if last else "1"

    db_obj = ShortURL(
        original_url=payload.original_url,
        short_code=short_code,
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@app.get("/{short_code}", response_class=RedirectResponse)
async def redirect(short_code: str, db: SessionLocal = Depends(get_db)):
    record = (
        db.query(ShortURL)
        .filter(ShortURL.short_code == short_code, ShortURL.is_active == True)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Short URL not found or inactive")
    return RedirectResponse(url=record.original_url, status_code=302)


@app.get("/api/urls", response_model=List[ShortURLResponse])
async def list_urls(db: SessionLocal = Depends(get_db)):
    return db.query(ShortURL).filter(ShortURL.is_active == True).all()


@app.delete("/{short_code}", response_model=ShortURLResponse)
async def deactivate_url(short_code: str, db: SessionLocal = Depends(get_db)):
    record = db.query(ShortURL).filter(ShortURL.short_code == short_code).first()
    if not record:
        raise HTTPException(status_code=404, detail="Short URL not found")
    record.is_active = False
    db.commit()
    db.refresh(record)
    return record
```

```markpact:run python
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```