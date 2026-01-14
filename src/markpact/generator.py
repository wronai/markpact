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
    temperature: float = 0.7
    max_tokens: int = 4096
    
    @classmethod
    def from_env(cls) -> "GeneratorConfig":
        """Load config from environment variables"""
        return cls(
            model=os.environ.get("MARKPACT_MODEL", "ollama/qwen2.5-coder:14b"),
            api_base=os.environ.get("MARKPACT_API_BASE", "http://localhost:11434"),
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

## CRITICAL FORMAT - Follow EXACTLY:

```markpact:deps python
package1
package2
```

```markpact:file python path=app/main.py
# actual code here
```

```markpact:run python
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```

## RULES:
1. Each markpact block MUST be a proper fenced code block with triple backticks
2. Dependencies: one package per line, no extras
3. Files: include `path=` in the header line
4. Run: single command to start the app
5. Use `${MARKPACT_PORT:-8000}` for ports
6. Generate COMPLETE working code - no TODOs or placeholders
7. Use Python 3.10+ with type hints

## OUTPUT STRUCTURE:
# Project Title

Brief description.

## Endpoints / Features
- list them here

---

```markpact:deps python
...
```

```markpact:file python path=app/main.py
...complete code...
```

```markpact:run python
...
```

Generate ONLY the README content. Start with # Title."""


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
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate a Markpact README for:\n\n{prompt}"},
    ]
    
    try:
        response = litellm.completion(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        
        content = response.choices[0].message.content
        
        # Clean up response (remove markdown code fences if wrapped)
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        return content.strip()
        
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
    "todo-api": "REST API do zarządzania zadaniami (todo) z SQLite i pełnym CRUD. FastAPI + SQLAlchemy.",
    "blog-api": "API bloga z postami i komentarzami. Endpoints: GET/POST /posts, GET/POST /posts/{id}/comments.",
    "url-shortener": "Skracacz URL z FastAPI. POST /shorten z URL, GET /{code} przekierowuje na oryginalny URL.",
    "weather-cli": "CLI do sprawdzania pogody. Używa requests i typer. Pobiera dane z wttr.in.",
    "file-server": "Prosty serwer plików z FastAPI. Upload, download, lista plików. Przechowuje w ./uploads/",
    "calculator-api": "Kalkulator REST API. Endpoints: POST /add, /subtract, /multiply, /divide z JSON body.",
}


def get_example_prompt(name: str) -> str:
    """Get example prompt by name."""
    return EXAMPLE_PROMPTS.get(name, name)


def list_example_prompts() -> dict[str, str]:
    """List all available example prompts."""
    return EXAMPLE_PROMPTS.copy()
