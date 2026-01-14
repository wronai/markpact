# Markpact – Dokumentacja

Markpact to minimalny runtime pozwalający trzymać cały projekt w jednym `README.md`.

## Spis treści

- [Szybki start](#szybki-start)
- [CLI Reference](#cli-reference)
- [Konwersja Markdown](#konwersja-markdown)
- [Generowanie z LLM](generator.md) ⭐ **NEW**
- [Kontrakt markpact:*](contract.md)
- [Integracja CI/CD](ci-cd.md)
- [Współpraca z LLM](llm.md)
- [Publikacja pakietu](publishing.md)

## Szybki start

### Instalacja

```bash
# Z PyPI
pip install markpact

# Lub lokalnie (dev)
git clone https://github.com/wronai/markpact.git
cd markpact
pip install -e .
```

### Podstawowe użycie

```bash
# Uruchom projekt z README
markpact README.md

# Podgląd bez wykonywania
markpact README.md --dry-run

# Własny katalog sandbox
markpact README.md --sandbox ./my-sandbox

# Tryb cichy
markpact README.md --quiet
```

## CLI Reference

```
markpact [OPTIONS] [README]
markpact config [CONFIG_OPTIONS]

Argumenty:
  README                 Ścieżka do pliku Markdown (domyślnie: README.md)

Podstawowe opcje:
  -s, --sandbox DIR      Katalog sandbox (domyślnie: ./sandbox)
  -n, --dry-run          Pokaż co zostanie wykonane, bez uruchamiania
  -q, --quiet            Tryb cichy (bez komunikatów)
  -V, --version          Pokaż wersję
  -h, --help             Pokaż pomoc

Konwersja Markdown:
  -c, --convert          Konwertuj zwykły Markdown do markpact i uruchom
  --convert-only         Tylko konwertuj i wyświetl wynik
  --save-converted FILE  Zapisz skonwertowany plik
  -a, --auto             Auto-detekcja: konwertuj jeśli brak markpact blocks

Generowanie z LLM:
  -p, --prompt TEXT      Generuj kontrakt z opisu tekstowego
  -o, --output FILE      Plik wyjściowy (domyślnie: README.md)
  -m, --model MODEL      Model LLM (nadpisuje config)
  --api-base URL         URL API (nadpisuje config)
  --api-key KEY          API key (nadpisuje config)
  -e, --example NAME     Użyj gotowego przykładu (zobacz --list-examples)
  --list-examples        Pokaż dostępne przykłady
  -r, --run              Uruchom natychmiast po wygenerowaniu
  --docker               Uruchom w kontenerze Docker

Auto-fix:
  --auto-fix             Auto-naprawa błędów runtime (domyślnie włączone)
  --no-auto-fix          Wyłącz auto-naprawę błędów

Testowanie:
  -t, --test             Uruchom testy z bloków markpact:test
  --test-only            Tylko uruchom testy (zatrzymaj serwis po testach)

Publikacja:
  --publish              Publikuj do rejestru (markpact:publish block)
  --bump TYPE            Bump wersji przed publikacją (major, minor, patch)
  --registry NAME        Nadpisz rejestr (pypi, npm, docker, github, ghcr)

Konfiguracja (markpact config):
  --init                 Utwórz plik konfiguracyjny ~/.markpact/.env
  --force                Nadpisz istniejący plik konfiguracyjny
  --provider NAME        Zastosuj preset providera (ollama, openrouter, openai, anthropic, groq)
  --list-providers       Lista dostępnych providerów
  --model MODEL          Ustaw model LLM
  --api-key KEY          Ustaw API key
  --api-base URL         Ustaw API base URL
```

### Przykłady użycia

```bash
# Uruchom projekt
markpact README.md

# Konfiguracja LLM
markpact config --init
markpact config --provider openrouter --api-key sk-or-v1-xxxxx

# Wygeneruj nowy projekt z LLM
markpact -p "REST API do zadań z SQLite" -o todo/README.md

# Wygeneruj i uruchom natychmiast (one-liner)
markpact -p "URL shortener z FastAPI" -o url/README.md --run

# Uruchom w Docker
markpact todo/README.md --docker
```

## Konwersja Markdown

Markpact może automatycznie konwertować zwykłe pliki Markdown (bez tagów `markpact:*`):

```bash
# Podgląd konwersji
markpact sample.md --convert-only

# Konwertuj i uruchom
markpact sample.md --convert

# Auto-detekcja (konwertuj jeśli brak markpact blocks)
markpact sample.md --auto

# Zapisz wynik konwersji
markpact sample.md --convert-only --save-converted output.md
```

### Heurystyki detekcji

| Wykryte | Konwertowane na | Przykład |
|---------|-----------------|----------|
| Lista pakietów | `markpact:deps python` | `fastapi`, `requests>=2.0` |
| Kod Python | `markpact:file python path=...` | `import`, `def`, `class` |
| Kod JavaScript | `markpact:file javascript path=...` | `const`, `require`, `import` |
| HTML | `markpact:file html path=...` | `<!DOCTYPE`, `<html>` |
| Komendy bash | `markpact:run bash` | `python`, `uvicorn`, `npm` |

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

## Publikacja do rejestrów

Markpact umożliwia publikację artefaktów do różnych rejestrów bezpośrednio z README.

### Blok `markpact:publish`

```markdown
```markpact:publish
registry = pypi
name = my-package
version = 0.1.0
description = Mój pakiet
author = Twoje Imię
license = MIT
keywords = example, demo
repository = https://github.com/user/repo
\```
```

### Obsługiwane rejestry

| Rejestr | Wartość `registry` | Opis |
|---------|-------------------|------|
| PyPI | `pypi` | Python Package Index |
| TestPyPI | `pypi-test` | PyPI testowy |
| npm | `npm` | Node.js packages |
| Docker Hub | `docker` | Obrazy Docker |
| GitHub Packages | `github` | GitHub npm |
| GHCR | `ghcr` | GitHub Container Registry |

### Użycie

```bash
# Podgląd bez publikacji
markpact README.md --publish --dry-run

# Publikacja do PyPI
markpact README.md --publish

# Publikacja z bump wersji
markpact README.md --publish --bump patch  # 0.1.0 -> 0.1.1
markpact README.md --publish --bump minor  # 0.1.0 -> 0.2.0
markpact README.md --publish --bump major  # 0.1.0 -> 1.0.0

# Nadpisanie rejestru
markpact README.md --publish --registry docker
```

### Przykłady

- [PyPI Publish](../examples/pypi-publish/) - Python packages
- [npm Publish](../examples/npm-publish/) - Node.js packages  
- [Docker Publish](../examples/docker-publish/) - Docker images

## Testowanie API

Markpact umożliwia definiowanie testów HTTP bezpośrednio w README:

```markdown
```markpact:test http
# Health check
GET /health EXPECT 200

# Test API
POST /shorten BODY {"url":"https://example.com"} EXPECT 200
GET /abc123 EXPECT 301
\```
```

### Uruchamianie testów

```bash
# Uruchom testy (serwis startuje automatycznie)
markpact README.md --test-only

# Generuj z testami i uruchom
markpact -e url-shortener -o url/README.md --test-only
```

### Format testów HTTP

```
METHOD /path EXPECT status_code
METHOD /path BODY {"json":"data"} EXPECT status_code
```

Przykłady:
- `GET /health EXPECT 200`
- `POST /users BODY {"name":"John"} EXPECT 201`
- `DELETE /users/1 EXPECT 204`

### Wynik testów

```
============================================================
TEST RESULTS: 2/3 passed
============================================================
  ✓ GET /health: Status 200 (expected 200)
  ✓ POST /shorten: Status 200 (expected 200)
  ✗ GET /abc: Status 404 (expected 301)
```

## Linki

- [Przykłady](../examples/)
- [TODO / Roadmap](../TODO.md)
- [Changelog](../CHANGELOG.md)
