# Kontrakt markpact:*

## Typy codeblocków

### `markpact:bootstrap <lang>`

Wbudowany runtime parsujący README i wykonujący pozostałe bloki.

```markdown
```markpact:bootstrap python
#!/usr/bin/env python3
# kod bootstrapu...
\```
```

**Zasady:**
- Dokładnie jeden bootstrap na README
- Musi być pierwszym fenced codeblockiem
- `<lang>` określa interpreter (obecnie tylko `python`)

---

### `markpact:deps <scope>`

Lista zależności dla danego scope.

```markdown
```markpact:deps python
fastapi>=0.100
uvicorn
pydantic
\```
```

**Scope:**
- `python` – generuje `requirements.txt`, instaluje przez pip
- `node` (planowane) – generuje `package.json`
- `system` (planowane) – apt/brew

**Zasady:**
- Jedna zależność na linię
- Puste linie ignorowane
- Wspierane wersjonowanie (`==`, `>=`, `<`, etc.)

---

### `markpact:file <lang> path=<ścieżka>`

Tworzy plik w sandboxie.

```markdown
```markpact:file python path=app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"hello": "world"}
\```
```

**Metadane:**
- `path=...` – **wymagane**, ścieżka względem sandboxu
- `<lang>` – opcjonalne, informacyjne (syntax highlighting)

**Planowane:**
- `mode=...` – uprawnienia (np. `755`)
- `encoding=...` – kodowanie (domyślnie UTF-8)

---

### `markpact:run <lang>`

Komenda uruchomieniowa.

```markdown
```markpact:run python
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
\```
```

**Zasady:**
- Dokładnie jedna komenda `run` na README
- Wykonywana w sandboxie (`cwd=SANDBOX`)
- Może używać zmiennych środowiskowych
- Shell expansion działa (`${VAR:-default}`)

---

## Planowane typy

### `markpact:config`

```markdown
```markpact:config
sandbox: ./my-sandbox
port: 8080
env:
  DEBUG: "1"
\```
```

### `markpact:test`

```markdown
```markpact:test python
pytest tests/ -v
\```
```

### `markpact:ignore`

```markdown
```markpact:ignore
Ten blok jest ignorowany przez runtime.
Przydatne do dokumentacji wewnętrznej.
\```
```
