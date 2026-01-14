# Markpact – Dokumentacja

Markpact to minimalny runtime pozwalający trzymać cały projekt w jednym `README.md`.

## Spis treści

- [Szybki start](#szybki-start)
- [Kontrakt markpact:*](contract.md)
- [Integracja CI/CD](ci-cd.md)
- [Współpraca z LLM](llm.md)

## Szybki start

### Instalacja

```bash
pip install markpact
```

### Użycie

```bash
# Uruchom projekt z README
markpact README.md

# Podgląd bez wykonywania
markpact README.md --dry-run

# Własny katalog sandbox
markpact README.md -s ./my-sandbox
```

### Zmienne środowiskowe

| Zmienna | Opis | Domyślnie |
|---------|------|-----------|
| `MARKPACT_SANDBOX` | Katalog sandbox | `./sandbox` |
| `MARKPACT_NO_VENV` | Wyłącz tworzenie venv (`1`) | - |
| `MARKPACT_PORT` | Port dla aplikacji (używane w run) | - |

## Struktura README

```markdown
# Mój Projekt

Opis projektu (ignorowany przez markpact).

```markpact:deps python
fastapi
uvicorn
\```

```markpact:file python path=app/main.py
from fastapi import FastAPI
app = FastAPI()
\```

```markpact:run python
uvicorn app.main:app --port 8000
\```
```

## Kolejność wykonania

1. Parsowanie wszystkich codeblocków `markpact:*`
2. Tworzenie plików (`markpact:file`)
3. Instalacja zależności (`markpact:deps`)
4. Uruchomienie komendy (`markpact:run`)

## Linki

- [Przykłady](../examples/)
- [TODO / Roadmap](../TODO.md)
- [Changelog](../CHANGELOG.md)
