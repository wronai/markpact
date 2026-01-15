"""Markpact contract generator using LiteLLM"""

import json
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Suppress Pydantic serialization warnings from litellm
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

try:
    import litellm
    litellm.suppress_debug_info = True
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


@dataclass
class GeneratorConfig:
    """Configuration for LLM generator"""
    model: str = "ollama/qwen2.5-coder:14b"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    
    @classmethod
    def from_env(cls) -> "GeneratorConfig":
        """Load config from environment variables"""
        return cls(
            model=os.environ.get("MARKPACT_MODEL", "ollama/qwen2.5-coder:14b"),
            api_base=os.environ.get("MARKPACT_API_BASE", "http://localhost:11434"),
            api_key=os.environ.get("MARKPACT_API_KEY", ""),
            temperature=float(os.environ.get("MARKPACT_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("MARKPACT_MAX_TOKENS", "4096")),
        )
    
    @classmethod
    def from_file(cls, path: Path) -> "GeneratorConfig":
        """Load config from JSON file"""
        if not path.exists():
            return cls.from_env()
        data = json.loads(path.read_text())
        return cls(**data)


SYSTEM_PROMPT = """You are a Markpact contract generator. Generate executable README.md files.

## CRITICAL FORMAT RULES:

1. EVERY code block MUST have opening ``` AND closing ``` on separate lines
2. Use exactly this format for each block type:

### Dependencies block:
```text markpact:deps python
fastapi
uvicorn
sqlalchemy
```

### File block (MUST include path=):
```python markpact:file path=app/main.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
```

### Run block (MUST be properly closed):
```bash markpact:run
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```

### Test block (HTTP tests for the API):
```text markpact:test http
# Health check
GET /health EXPECT 200

# Test main endpoints
POST /endpoint BODY {"key": "value"} EXPECT 200
GET /endpoint/1 EXPECT 200
```

## IMPORTANT:
- ALWAYS close EVERY code block with ``` on its own line
- Use ${MARKPACT_PORT:-8000} for configurable ports
- Generate COMPLETE working code - no TODOs, no placeholders, no "..."
- Use Python 3.10+ with type hints and Pydantic models
- For FastAPI: use proper Request/Response models, not raw request.json()

## OUTPUT STRUCTURE:
```
# Project Title

Brief description.

## Features
- feature 1
- feature 2

## API Endpoints
- POST /endpoint - description
- GET /endpoint - description

---

```text markpact:deps python
dep1
dep2
```

```python markpact:file path=app/main.py
# complete working code with /health endpoint
```

```bash markpact:run
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```

```text markpact:test http
# Health check
GET /health EXPECT 200

# Test API endpoints
POST /endpoint BODY {"data": "test"} EXPECT 200
GET /endpoint/1 EXPECT 200
```
```

IMPORTANT RULES:
1. ALWAYS include a GET /health endpoint returning {"status": "ok"}
2. ALWAYS include a markpact:test block with HTTP tests
3. Close ALL code blocks with ```

Generate ONLY the README.md content. Start with # Title."""


def _fix_unclosed_blocks(content: str) -> str:
    """Fix unclosed code blocks in generated content."""
    lines = content.split('\n')
    in_code_block = False
    last_code_start = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('```') and not in_code_block:
            in_code_block = True
            last_code_start = i
        elif stripped == '```' and in_code_block:
            in_code_block = False
    
    # If still in a code block, close it
    if in_code_block:
        lines.append('```')
    
    return '\n'.join(lines)


def generate_contract(
    prompt: str,
    config: Optional[GeneratorConfig] = None,
    verbose: bool = False,
) -> str:
    """Generate a markpact contract from a text prompt.
    
    Args:
        prompt: Description of the project to generate
        config: LLM configuration (uses defaults if None)
        verbose: Print generation progress
        
    Returns:
        Generated README.md content
        
    Raises:
        ImportError: If litellm is not installed
        RuntimeError: If generation fails
    """
    if not LITELLM_AVAILABLE:
        raise ImportError(
            "litellm is required for contract generation. "
            "Install with: pip install markpact[llm]"
        )
    
    if config is None:
        config = GeneratorConfig.from_env()
    
    if verbose:
        print(f"[markpact] Using model: {config.model}")
        print(f"[markpact] API base: {config.api_base}")
        print(f"[markpact] Generating contract for: {prompt[:50]}...")
    
    # Configure litellm
    if config.api_base:
        litellm.api_base = config.api_base
    
    # Set API key for the provider
    if config.api_key:
        # LiteLLM uses different env vars for different providers
        if "openrouter" in config.model.lower():
            os.environ["OPENROUTER_API_KEY"] = config.api_key
        elif "openai" in config.model.lower() or config.model.startswith("gpt"):
            os.environ["OPENAI_API_KEY"] = config.api_key
        elif "anthropic" in config.model.lower() or "claude" in config.model.lower():
            os.environ["ANTHROPIC_API_KEY"] = config.api_key
        elif "groq" in config.model.lower():
            os.environ["GROQ_API_KEY"] = config.api_key
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate a Markpact README for:\n\n{prompt}"},
    ]
    
    try:
        # Build completion kwargs
        completion_kwargs = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        
        # Add API key directly if provided
        if config.api_key:
            completion_kwargs["api_key"] = config.api_key
        
        response = litellm.completion(**completion_kwargs)
        
        content = response.choices[0].message.content
        
        # Clean up response (remove markdown code fences if wrapped)
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Fix unclosed code blocks - ensure last markpact block is closed
        content = _fix_unclosed_blocks(content)
        
        return content
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate contract: {e}") from e


def save_contract(content: str, output_path: Path, verbose: bool = False) -> Path:
    """Save generated contract to file.
    
    Args:
        content: Generated README content
        output_path: Where to save the file
        verbose: Print save location
        
    Returns:
        Path to saved file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    
    if verbose:
        print(f"[markpact] Saved contract to: {output_path}")
    
    return output_path


# Example prompts for testing
EXAMPLE_PROMPTS = {
    # REST APIs
    "todo-api": "REST API do zarządzania zadaniami (todo) z SQLite i pełnym CRUD. FastAPI + SQLAlchemy. Endpoints: GET/POST/PUT/DELETE /tasks",
    "blog-api": "API bloga z postami i komentarzami. FastAPI + SQLite. Endpoints: GET/POST /posts, GET/POST /posts/{id}/comments, DELETE /posts/{id}",
    "url-shortener": "Skracacz URL z FastAPI i SQLite. POST /shorten przyjmuje {url}, zwraca {short_url}. GET /{code} przekierowuje 301.",
    "user-auth": "API autentykacji użytkowników. FastAPI + SQLite + passlib. POST /register, POST /login (zwraca JWT), GET /me (wymaga tokena)",
    "notes-api": "API do notatek z tagami. FastAPI + SQLite. CRUD dla /notes, filtrowanie po tagach, wyszukiwanie pełnotekstowe",
    "inventory-api": "API do zarządzania magazynem. FastAPI + SQLite. Produkty, kategorie, stany magazynowe, historia zmian",
    
    # Utilities
    "calculator-api": "Kalkulator REST API. FastAPI. Endpoints: POST /calculate z {operation, a, b}. Obsługa +, -, *, /, sqrt, pow",
    "file-server": "Serwer plików z FastAPI. POST /upload (multipart), GET /files (lista), GET /files/{name} (download), DELETE /files/{name}",
    "image-resize": "API do zmiany rozmiaru obrazów. FastAPI + Pillow. POST /resize z obrazem i wymiarami, zwraca przeskalowany obraz",
    "qr-generator": "Generator kodów QR. FastAPI + qrcode. POST /generate z {text}, zwraca obraz PNG kodu QR",
    
    # CLI tools
    "weather-cli": "CLI do sprawdzania pogody. Typer + requests. Pobiera dane z wttr.in. Kolorowy output z rich.",
    "file-organizer": "CLI do organizacji plików. Typer + rich. Sortuje pliki wg rozszerzenia do podfolderów.",
    "csv-analyzer": "CLI do analizy plików CSV. Typer + pandas + rich. Statystyki, filtrowanie, eksport.",
    
    # Web apps
    "chat-websocket": "Prosty chat WebSocket. FastAPI + websockets. Endpoint /ws dla połączeń, broadcast wiadomości.",
    "pastebin": "Pastebin clone. FastAPI + SQLite. POST /paste tworzy paste, GET /paste/{id} zwraca treść, syntax highlighting",
    "link-checker": "API do sprawdzania linków. FastAPI + httpx. POST /check z {urls[]}, zwraca status każdego URL",
}


def get_example_prompt(name: str) -> str:
    """Get example prompt by name."""
    return EXAMPLE_PROMPTS.get(name, name)


def list_example_prompts() -> dict[str, str]:
    """List all available example prompts."""
    return EXAMPLE_PROMPTS.copy()
