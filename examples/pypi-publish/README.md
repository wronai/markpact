# PyPI Publish Example

Przykład publikacji paczki Python do PyPI bezpośrednio z README.

## Użycie

```bash
# Podgląd bez publikacji
markpact examples/pypi-publish/README.md --publish --dry-run

# Publikacja do TestPyPI
markpact examples/pypi-publish/README.md --publish --registry pypi-test

# Publikacja do PyPI z bump wersji
markpact examples/pypi-publish/README.md --publish --bump patch

# Publikacja do PyPI (produkcja)
markpact examples/pypi-publish/README.md --publish
```

## Konfiguracja

Upewnij się, że masz skonfigurowany `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-xxxx

[testpypi]
username = __token__
password = pypi-xxxx
```

---

```markpact:publish
registry = pypi
name = markpact-example-pypi
version = 0.1.1
description = Example package published with markpact
author = Your Name
license = MIT
keywords = example, markpact, demo
repository = https://github.com/your/repo
```

```markpact:file python path=markpact_example_pypi/__init__.py
"""Example package published with markpact"""

__version__ = "0.1.0"

def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

```markpact:file python path=markpact_example_pypi/cli.py
"""CLI for example package"""

import argparse
from . import hello, add

def main():
    parser = argparse.ArgumentParser(description="Example CLI")
    parser.add_argument("--name", default="World", help="Name to greet")
    parser.add_argument("--add", nargs=2, type=int, help="Add two numbers")
    
    args = parser.parse_args()
    
    if args.add:
        result = add(args.add[0], args.add[1])
        print(f"{args.add[0]} + {args.add[1]} = {result}")
    else:
        print(hello(args.name))

if __name__ == "__main__":
    main()
```

```markpact:test http
# No HTTP tests for CLI package
```
