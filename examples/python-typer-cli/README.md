# Python Typer CLI Example

Minimalne CLI w Pythonie (Typer) uruchamiane przez Markpact.

## Uruchomienie

```bash
markpact examples/python-typer-cli/README.md
```

---

```text markpact:deps python
typer
rich
```

```python markpact:file path=app/main.py
import typer
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def hello(name: str = "World") -> None:
    console.print(f"Hello, [bold]{name}[/bold]!")

@app.command()
def add(a: int, b: int) -> None:
    console.print(f"{a} + {b} = [green]{a + b}[/green]")

if __name__ == "__main__":
    app()
```

```bash markpact:run
python app/main.py hello --name ${MARKPACT_NAME:-World}
```

```bash markpact:test shell
python app/main.py hello --name Test
python app/main.py add 2 3
```
