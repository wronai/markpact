# Generowanie kontraktów z LLM

Markpact może generować kompletne kontrakty README.md na podstawie opisu tekstowego, wykorzystując lokalne lub zdalne modele LLM przez LiteLLM.

## Instalacja

```bash
pip install markpact[llm]
```

## Szybki start

```bash
# Generuj z promptu
markpact -p "REST API do zarządzania zadaniami z SQLite i pełnym CRUD."

# Generuj do konkretnego pliku
markpact -p "Blog API z FastAPI" -o my-blog/README.md

# Użyj gotowego przykładu
markpact -e todo-api -o todo-project/README.md

# Lista dostępnych przykładów
markpact --list-examples
```

## Konfiguracja modelu

### Zmienne środowiskowe

| Zmienna | Opis | Domyślnie |
|---------|------|-----------|
| `MARKPACT_MODEL` | Model LLM | `ollama/qwen2.5-coder:7b` |
| `MARKPACT_API_BASE` | URL API | `http://localhost:11434` |
| `MARKPACT_TEMPERATURE` | Temperatura (0-1) | `0.7` |
| `MARKPACT_MAX_TOKENS` | Max tokenów odpowiedzi | `4096` |

### Flagi CLI

```bash
markpact -p "..." --model ollama/codellama:7b
markpact -p "..." --api-base http://localhost:11434
```

## Obsługiwane modele

### Lokalne (Ollama)

```bash
# Zainstaluj Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pobierz model
ollama pull qwen2.5-coder:7b

# Uruchom markpact
markpact -p "REST API dla książek" -m ollama/qwen2.5-coder:7b
```

Rekomendowane modele Ollama:
- `ollama/qwen2.5-coder:7b` (domyślny) – szybki, dobry dla kodu
- `ollama/codellama:7b` – Meta Code Llama
- `ollama/deepseek-coder:6.7b` – DeepSeek Coder
- `ollama/mistral:7b` – ogólny model

### OpenAI

```bash
export OPENAI_API_KEY=sk-...
markpact -p "..." -m openai/gpt-4o
```

### Anthropic

```bash
export ANTHROPIC_API_KEY=sk-ant-...
markpact -p "..." -m anthropic/claude-3-sonnet
```

### Azure OpenAI

```bash
export AZURE_API_KEY=...
export AZURE_API_BASE=https://your-resource.openai.azure.com/
markpact -p "..." -m azure/gpt-4
```

## Przykłady promptów

```bash
# API
markpact -p "REST API do zarządzania użytkownikami z JWT auth"
markpact -p "GraphQL API dla e-commerce z produktami i zamówieniami"

# Web apps
markpact -p "Dashboard Streamlit do wizualizacji danych CSV"
markpact -p "Prosta aplikacja Flask z logowaniem użytkowników"

# CLI
markpact -p "CLI do konwersji formatów obrazów (PNG, JPG, WebP)"
markpact -p "Narzędzie CLI do backupu baz danych PostgreSQL"

# Mikrousługi
markpact -p "Serwis kolejkowy z Redis i FastAPI"
markpact -p "Worker do przetwarzania obrazów z Celery"
```

## Gotowe przykłady (--list-examples)

```bash
markpact --list-examples
```

| Nazwa | Opis |
|-------|------|
| `todo-api` | REST API do zarządzania zadaniami z SQLite |
| `blog-api` | API bloga z postami i komentarzami |
| `url-shortener` | Skracacz URL z FastAPI |
| `weather-cli` | CLI do sprawdzania pogody |
| `file-server` | Prosty serwer plików |
| `calculator-api` | Kalkulator REST API |

Użycie:
```bash
markpact -e todo-api -o my-todo/README.md
markpact my-todo/README.md  # uruchom
```

## Plik konfiguracyjny

Utwórz `markpact.config.json` w katalogu projektu:

```json
{
  "model": "ollama/qwen2.5-coder:7b",
  "api_base": "http://localhost:11434",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

## Wskazówki

### Dobre prompty

- **Bądź konkretny**: "REST API z CRUD" → "REST API do zarządzania produktami z pełnym CRUD, SQLite, walidacją Pydantic"
- **Określ technologie**: "...z FastAPI, SQLAlchemy, Alembic"
- **Podaj kontekst**: "API dla aplikacji mobilnej do śledzenia wydatków"

### Iteracja

```bash
# Wygeneruj
markpact -p "..." -o project/README.md

# Przejrzyj
cat project/README.md

# Uruchom
markpact project/README.md
```

## Troubleshooting

### "litellm not installed"

```bash
pip install markpact[llm]
# lub
pip install litellm
```

### "Connection refused" (Ollama)

```bash
# Sprawdź czy Ollama działa
ollama list
curl http://localhost:11434/api/tags

# Uruchom Ollama
ollama serve
```

### Pusty lub niepełny output

- Zwiększ `MARKPACT_MAX_TOKENS`
- Użyj większego modelu (7b → 13b)
- Uprość prompt
