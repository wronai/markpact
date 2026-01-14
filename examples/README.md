# Markpact Examples

Przykłady demonstracyjne różnych typów aplikacji uruchamianych przez Markpact.

## Uruchamianie przykładów

```bash
# Zainstaluj markpact
pip install markpact

# Uruchom wybrany przykład
markpact examples/<nazwa>/README.md
```

## Lista przykładów

| Przykład | Typ | Opis | Technologie |
|----------|-----|------|-------------|
| [fastapi-todo](fastapi-todo/) | Web API | REST API z CRUD i SQLite | FastAPI, SQLAlchemy, Pydantic |
| [flask-blog](flask-blog/) | Web App | Blog z szablonami Jinja2 | Flask, SQLite, Pico CSS |
| [cli-tool](cli-tool/) | CLI | Narzędzie do organizacji plików | Click, Rich |
| [streamlit-dashboard](streamlit-dashboard/) | Dashboard | Interaktywny dashboard danych | Streamlit, Pandas, Plotly |
| [kivy-mobile](kivy-mobile/) | Mobile | Kalkulator BMI (Android/iOS) | Kivy, Buildozer |
| [electron-desktop](electron-desktop/) | Desktop | Notatnik Markdown | Electron, Node.js |
| [markdown-converter](markdown-converter/) | Converter | Konwersja zwykłego Markdown do markpact | `--convert`, `--auto` |

## Struktura przykładu

Każdy przykład to osobny folder z `README.md` zawierającym:

```markdown
# Nazwa projektu

Opis projektu.

## Uruchomienie
```bash
markpact examples/<nazwa>/README.md
\```

---

```markpact:deps python
zależność1
zależność2
\```

```markpact:file python path=plik.py
# kod pliku
\```

```markpact:run python
komenda uruchomieniowa
\```
```

## Tworzenie własnego przykładu

1. Utwórz folder `examples/<nazwa>/`
2. Utwórz `README.md` z codeblockami `markpact:*`
3. Przetestuj: `markpact examples/<nazwa>/README.md --dry-run`
4. Uruchom: `markpact examples/<nazwa>/README.md`

## Porty

| Przykład | Domyślny port |
|----------|---------------|
| fastapi-todo | 8001 |
| flask-blog | 5000 |
| streamlit-dashboard | 8501 |
| kivy-mobile | (okno GUI) |
| electron-desktop | (okno GUI) |

Zmiana portu:
```bash
MARKPACT_PORT=9000 markpact examples/fastapi-todo/README.md
```
