# URL Shortener with FastAPI and SQLite

A minimal URL shortener API built with FastAPI and SQLite.  
It provides endpoints to create short links and resolve them back to the original URLs.

## Features
- Create short links via POST `/shorten`
- Resolve short links via GET `/{short_code}`
- Persistent storage using SQLite via SQLAlchemy
- Pydantic validation for request/response models
- Type‑annotated, ready‑to‑run FastAPI application

## API Endpoints
- `POST /shorten` - Create a new short link
- `GET /{short_code}` - Retrieve the original URL for a short code
- `DELETE /{short_code}` - (Optional) Delete a short link

---

```text markpact:deps python
fastapi
uvicorn
sqlalchemy
pydantic
```

```python markpact:file path=app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Dict

# ---------- Database Setup ----------
SQLALCHEMY_DATABASE_URL = "sqlite:///./shortener.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ShortURL(Base):
    __tablename__ = "short_urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True, nullable=False)
    original_url = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)

# ---------- Pydantic Models ----------
class ShortenRequest(BaseModel):
    url: str = Field(..., example="https://example.com/very/long/url")


class ShortenResponse(BaseModel):
    short_code: str
    full_url: str


# ---------- Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- FastAPI App ----------
app = FastAPI()


# Helper to generate a short code (simple base36)
def generate_short_code(length: int = 6) -> str:
    import uuid
    unique_id = uuid.uuid4().int & ((1 << 36) - 1)
    return str(unique_id)[:length]


# ---------- Routes ----------
@app.post("/shorten", response_model=ShortenResponse)
async def create_short_link(
    request: ShortenRequest, db: SessionLocal = Depends(get_db)
):
    # Validate URL scheme
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    # Check if URL already exists to avoid duplicates
    existing = db.query(ShortURL).filter_by(original_url=request.url).first()
    if existing:
        raise HTTPException(status_code=409, detail="URL already shortened")

    short_code = generate_short_code()
    db_entry = ShortURL(short_code=short_code, original_url=request.url)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return ShortenResponse(short_code=short_code, full_url=request.url)


@app.get("/{short_code}")
async def resolve_short_link(short_code: str, db: SessionLocal = Depends(get_db)):
    db_entry = db.query(ShortURL).filter_by(short_code=short_code).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(db_entry.original_url)


@app.delete("/{short_code}")
async def delete_short_link(short_code: str, db: SessionLocal = Depends(get_db)):
    db_entry = db.query(ShortURL).filter_by(short_code=short_code).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Short code not found")
    db.delete(db_entry)
    db.commit()
    return {"detail": "Short link deleted"}
```

```bash markpact:run
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8009}
```