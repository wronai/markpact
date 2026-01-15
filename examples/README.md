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
| [go-http-api](go-http-api/) | Web API | Minimalne REST API w Go | Go, net/http |
| [node-express-api](node-express-api/) | Web API | Minimalne REST API w Node.js | Node.js, Express |
| [static-frontend](static-frontend/) | Frontend | Statyczny frontend (HTML/CSS/JS) | HTML, CSS, JS |
| [python-typer-cli](python-typer-cli/) | CLI | CLI w Python (Typer) | Typer, Rich |
| [rust-axum-api](rust-axum-api/) | Web API | Minimalne REST API w Rust | Rust, Axum |
| [php-cli](php-cli/) | CLI | CLI w PHP | PHP |
| [react-typescript-spa](react-typescript-spa/) | Frontend | SPA React + TypeScript | React, TypeScript, Vite |
| [typescript-node-api](typescript-node-api/) | Web API | REST API w TypeScript (Node) | TypeScript, Express |
| [pypi-publish](pypi-publish/) | Publish | Publikacja paczki Python do PyPI | `--publish`, `--bump` |
| [npm-publish](npm-publish/) | Publish | Publikacja paczki Node.js do npm | `--publish`, `--registry` |
| [docker-publish](docker-publish/) | Publish | Budowanie i publikacja obrazu Docker | `--publish`, Docker |

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

```text markpact:deps python
zależność1
zależność2
\```

```python markpact:file path=plik.py
# kod pliku
\```

```bash markpact:run
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
| go-http-api | 8080 |
| node-express-api | 3000 |
| static-frontend | 8088 |
| python-typer-cli | (CLI) |
| rust-axum-api | 8081 |
| php-cli | (CLI) |
| react-typescript-spa | 3000 |
| typescript-node-api | 4000 |

Zmiana portu:
```bash
MARKPACT_PORT=9000 markpact examples/fastapi-todo/README.md
```
