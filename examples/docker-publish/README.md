# Docker Publish Example

Przykład budowania i publikacji obrazu Docker do rejestru bezpośrednio z README.

## Użycie

```bash
# Podgląd bez publikacji
markpact examples/docker-publish/README.md --publish --dry-run

# Buduj i publikuj do Docker Hub
markpact examples/docker-publish/README.md --publish

# Publikuj do GitHub Container Registry (ghcr.io)
markpact examples/docker-publish/README.md --publish --registry ghcr

# Publikuj z bump wersji
markpact examples/docker-publish/README.md --publish --bump patch
```

## Konfiguracja

### Docker Hub

```bash
docker login
```

### GitHub Container Registry

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

---

```toml markpact:publish
registry = docker
name = yourusername/example-api
version = 0.1.0
description = Example FastAPI service published with markpact
author = Your Name
license = MIT
```

```text markpact:deps python
fastapi
uvicorn
```

```python markpact:file path=app/main.py
"""Example FastAPI application for Docker publishing"""

from fastapi import FastAPI

app = FastAPI(
    title="Example API",
    description="Example API published as Docker image with markpact",
    version="0.1.0"
)

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Hello from Docker!", "version": "0.1.0"}

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/info")
def info():
    """API info endpoint"""
    return {
        "name": "example-api",
        "version": "0.1.0",
        "framework": "FastAPI",
        "published_with": "markpact"
    }
```

```dockerfile markpact:file path=Dockerfile
FROM python:3.12-slim

LABEL maintainer="Your Name"
LABEL version="0.1.0"
LABEL description="Example FastAPI service published with markpact"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash markpact:run
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```

```text markpact:test http
# Health check
GET /health EXPECT 200

# Root endpoint
GET / EXPECT 200

# Info endpoint
GET /info EXPECT 200
```
