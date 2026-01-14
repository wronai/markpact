# URL Shortener

A minimal FastAPI service that shortens URLs using SQLite as the backing store.  
Provides an endpoint to create short codes and redirects to the original URL.

## Endpoints / Features
- **POST /shorten** – Accepts a JSON `{ "url": "..." }` and returns a short URL.  
- **GET /{short_code}** – Redirects to the original long URL.  
- Uses an embedded SQLite database (`urls.db`) via SQLAlchemy.  

---

```markpact:deps python
fastapi
uvicorn
sqlalchemy
```

```markpact:file python path=app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import hashlib
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./urls.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class URLMap(Base):
    __tablename__ = "url_maps"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String, index=True)

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_short_code(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:8]

@app.post("/shorten")
async def shorten_url(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    original_url: str = payload.get("url")
    if not original_url:
        raise HTTPException(status_code=400, detail="URL is required")
    short_code = generate_short_code(original_url)
    # Handle rare collisions
    while db.get(URLMap, short_code) is not None:
        short_code = f"{short_code}_"
    db_entry = URLMap(short_code=short_code, original_url=original_url)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return {"short_url": f"{request.url_root}{short_code}"}

@app.get("/{short_code}")
async def redirect_url(short_code: str, db: Session = Depends(get_db)):
    db_entry = db.get(URLMap, short_code)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=db_entry.original_url)
```

```markpact:run python
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}