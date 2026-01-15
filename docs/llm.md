# Współpraca z LLM

Markpact jest zaprojektowany do współpracy z modelami językowymi (LLM).

## Zasada działania

LLM może generować lub edytować projekt poprzez modyfikacje README:
- Dodawanie/edycja codeblocków `markpact:file`
- Aktualizacja zależności w `markpact:deps`
- Zmiana komendy startowej w `markpact:run`

## Prompt dla LLM

```
Jesteś asystentem programistycznym pracującym z formatem Markpact.

Markpact pozwala zdefiniować cały projekt w jednym README.md używając codeblocków:

- `markpact:deps python` – lista zależności (jedna na linię)
- `markpact:file python path=<ścieżka>` – pełna zawartość pliku
- `markpact:run python` – komenda uruchomieniowa

Zasady:
1. Każdy `markpact:file` zawiera PEŁNĄ zawartość pliku (nie diff)
2. Zależności tylko w `markpact:deps` (nie w komentarzach)
3. Dokładnie jedna komenda w `markpact:run`
4. Ścieżki względne do sandboxu (np. `path=app/main.py`)

Użytkownik uruchomi projekt komendą: markpact README.md
```

## Przykład konwersacji

**User:** Stwórz REST API do zarządzania zadaniami

**LLM:**
```markdown
# Todo API

```text markpact:deps python
fastapi
uvicorn
pydantic
\```

```python markpact:file path=app/models.py
from pydantic import BaseModel

class Todo(BaseModel):
    id: int
    title: str
    done: bool = False
\```

```python markpact:file path=app/main.py
from fastapi import FastAPI
from app.models import Todo

app = FastAPI()
todos: list[Todo] = []

@app.get("/todos")
def list_todos():
    return todos

@app.post("/todos")
def create_todo(todo: Todo):
    todos.append(todo)
    return todo
\```

```bash markpact:run
uvicorn app.main:app --reload --port 8000
\```
```

## Walidacja przez LLM

LLM może walidować README przed uruchomieniem:

```
Sprawdź poprawność tego README w formacie Markpact:
- Czy wszystkie `markpact:file` mają `path=`?
- Czy zależności są poprawnie zadeklarowane?
- Czy komenda `run` jest poprawna?
- Czy importy w plikach są spójne z zależnościami?
```

## Iteracyjna edycja

```
User: Dodaj endpoint DELETE /todos/{id}

LLM: [modyfikuje tylko markpact:file path=app/main.py]
```

LLM powinien:
- Modyfikować tylko niezbędne bloki
- Zachowywać istniejące bloki bez zmian
- Podawać pełną zawartość modyfikowanego pliku

## Generowanie z opisu

```
User: Stwórz aplikację webową do śledzenia wydatków z:
- SQLite bazą danych
- Wykresami Chart.js
- Eksportem do CSV

LLM: [generuje kompletny README z markpact:deps, markpact:file, markpact:run]
```

## Best practices dla LLM

1. **Kompletność** – każdy plik musi być samodzielny
2. **Spójność** – importy muszą zgadzać się z plikami
3. **Zależności** – wszystkie biblioteki w `markpact:deps`
4. **Testowanie** – sugeruj `--dry-run` przed uruchomieniem
5. **Dokumentacja** – dodaj opis projektu w Markdown
