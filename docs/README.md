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
  -m, --model MODEL      Model LLM (domyślnie: ollama/qwen2.5-coder:7b)
  --api-base URL         URL API (domyślnie: http://localhost:11434)
  -e, --example NAME     Użyj gotowego przykładu (zobacz --list-examples)
  --list-examples        Pokaż dostępne przykłady
```

### Przykłady użycia

```bash
# Uruchom projekt
markpact README.md

# Wygeneruj nowy projekt z LLM
markpact -p "REST API do zadań z SQLite" -o todo/README.md

# Uruchom wygenerowany projekt
markpact todo/README.md
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

## Linki

- [Przykłady](../examples/)
- [TODO / Roadmap](../TODO.md)
- [Changelog](../CHANGELOG.md)
