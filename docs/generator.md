# Generowanie kontraktów z LLM

Markpact może generować kompletne kontrakty README.md na podstawie opisu tekstowego, wykorzystując lokalne lub zdalne modele LLM przez LiteLLM.

## Instalacja

```bash
pip install markpact[llm]
```

## Szybki start

```bash
# Zainicjuj konfigurację (tworzy ~/.markpact/.env)
markpact config --init

# Generuj z promptu
markpact -p "REST API do zarządzania zadaniami z SQLite i pełnym CRUD."

# Generuj do konkretnego pliku
markpact -p "Blog API z FastAPI" -o my-blog/README.md

# Użyj gotowego przykładu
markpact -e todo-api -o todo-project/README.md

# Lista dostępnych przykładów
markpact --list-examples
```

## Konfiguracja (markpact config)

Markpact przechowuje konfigurację LLM w pliku `~/.markpact/.env`.

### Inicjalizacja

```bash
# Utwórz plik konfiguracyjny z domyślnymi wartościami
markpact config --init

# Pokaż aktualną konfigurację
markpact config

# Wymuś nadpisanie istniejącej konfiguracji
markpact config --init --force
```

### Ustawianie wartości

```bash
# Ustaw model
markpact config --model openrouter/nvidia/nemotron-3-nano-30b-a3b:free

# Ustaw API key
markpact config --api-key sk-or-v1-xxxxx

# Ustaw API base URL
markpact config --api-base https://openrouter.ai/api/v1
```

### Presety providerów

```bash
# Lista dostępnych providerów
markpact config --list-providers

# Zastosuj preset (automatycznie ustawia model i API base)
markpact config --provider openrouter --api-key sk-or-v1-xxxxx
markpact config --provider openai --api-key sk-xxxxx
markpact config --provider ollama  # lokalny, bez klucza
```

### Plik konfiguracyjny (~/.markpact/.env)

```bash
# Markpact LLM Configuration
MARKPACT_MODEL="openrouter/nvidia/nemotron-3-nano-30b-a3b:free"
MARKPACT_API_BASE="https://openrouter.ai/api/v1"
MARKPACT_API_KEY="sk-or-v1-xxxxx"
MARKPACT_TEMPERATURE="0.7"
MARKPACT_MAX_TOKENS="4096"
```

## Obsługiwane providery

### Ollama (lokalny, domyślny)

```bash
markpact config --provider ollama
markpact -p "REST API dla książek"
```

### OpenRouter (darmowe modele!)

```bash
markpact config --provider openrouter --api-key sk-or-v1-xxxxx
markpact config --model openrouter/nvidia/nemotron-3-nano-30b-a3b:free
markpact -p "REST API dla książek"
```

Darmowe modele OpenRouter:
- `openrouter/nvidia/nemotron-3-nano-30b-a3b:free`
- `openrouter/meta-llama/llama-3.2-3b-instruct:free`
- `openrouter/mistralai/mistral-7b-instruct:free`

## One-liner: Generuj i uruchom

Wygeneruj i uruchom usługę jedną komendą:

```bash
# Generuj i uruchom natychmiast
markpact -p "REST API do zarządzania zadaniami" -o todo/README.md --run

# Z przykładu
markpact -e todo-api -o todo/README.md --run

# Z Docker sandbox (izolacja)
markpact -p "URL shortener z FastAPI" -o url/README.md --run --docker
```

### Przykłady one-liner

```bash
# Todo API - od tekstu do działającej usługi
markpact -p "REST API do zadań z SQLite, CRUD, FastAPI" -o /tmp/todo/README.md -r

# URL Shortener
markpact -e url-shortener -o /tmp/url/README.md -r

# Blog API z Docker
markpact -e blog-api -o /tmp/blog/README.md -r --docker

# Generator QR kodów
markpact -e qr-generator -o /tmp/qr/README.md -r
```

## Docker Sandbox

Uruchom w izolowanym kontenerze Docker:

```bash
# Generuj i uruchom w Docker
markpact -p "Chat WebSocket z FastAPI" -o chat/README.md --run --docker

# Uruchom istniejący projekt w Docker
markpact my-project/README.md --docker
```

Docker automatycznie:
- Tworzy `Dockerfile` w sandbox
- Buduje obraz `markpact-app`
- Uruchamia kontener na porcie 8000
- Udostępnia pod `http://localhost:8000`

### OpenAI

```bash
markpact config --provider openai --api-key sk-xxxxx
markpact -p "REST API dla książek"
```

### Anthropic

```bash
markpact config --provider anthropic --api-key sk-ant-xxxxx
markpact -p "REST API dla książek"
```

### Groq (szybkie, darmowe)

```bash
markpact config --provider groq --api-key gsk_xxxxx
markpact -p "REST API dla książek"
```

### Flagi CLI (nadpisują config)

```bash
markpact -p "..." --model ollama/codellama:7b
markpact -p "..." --api-base http://localhost:11434
markpact -p "..." --api-key sk-xxxxx
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
