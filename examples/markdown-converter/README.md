# Markdown Converter Example

Ten przykład pokazuje jak Markpact może automatycznie konwertować zwykłe pliki Markdown
do formatu `markpact:*` i uruchomić je bez modyfikacji oryginalnego pliku.

## Użycie konwertera

### 1. Podgląd konwersji (bez wykonywania)

```bash
markpact examples/markdown-converter/sample.md --convert-only
```

### 2. Konwersja i uruchomienie

```bash
markpact examples/markdown-converter/sample.md --convert
```

### 3. Auto-detekcja (jeśli brak markpact blocks)

```bash
markpact examples/markdown-converter/sample.md --auto
```

### 4. Zapisz skonwertowany plik

```bash
markpact examples/markdown-converter/sample.md --convert-only --save-converted output.md
```

## Jak działa konwerter?

1. **Analiza codeblocków** – Markpact analizuje wszystkie fenced code blocks
2. **Detekcja typu** – Na podstawie języka i zawartości określa typ:
   - `markpact:deps` – lista zależności (wykrywa pakiety Python/Node)
   - `markpact:file` – kod źródłowy (wykrywa importy, klasy, funkcje)
   - `markpact:run` – komenda uruchomieniowa (wykrywa python, uvicorn, npm, etc.)
3. **Sugestia nazw plików** – Dla bloków `file` sugeruje nazwę na podstawie zawartości
4. **Raport** – Wyświetla listę zmian i poziom pewności

## Heurystyki detekcji

### Dependencies (markpact:deps)
- Linie wyglądające jak pakiety: `fastapi`, `flask==2.0`, `requests>=2.28`
- Format `package==version`
- Brak importów/definicji funkcji

### Files (markpact:file)
- Język określony (python, javascript, html, css, etc.)
- Importy: `import x`, `from x import y`, `require()`
- Definicje: `def `, `class `, `function `, `const `
- Struktura HTML: `<!DOCTYPE`, `<html>`

### Run commands (markpact:run)
- Język: bash, sh, shell, console
- Komendy: `python`, `uvicorn`, `npm`, `node`, `flask`, `streamlit`

## Przykładowe pliki

- `sample.md` – zwykły Markdown bez tagów markpact
- `sample_converted.md` – wynik konwersji (generowany)

---

## Uruchomienie tego README

Ten README sam w sobie jest projektem markpact:

```text markpact:deps python
rich
```

```python markpact:file path=demo.py
from rich.console import Console
from rich.panel import Panel

console = Console()

console.print(Panel.fit(
    "[bold green]Markpact Converter Demo[/bold green]\n\n"
    "Ten skrypt został uruchomiony z README.md\n"
    "zawierającego tagi markpact:*\n\n"
    "[dim]Użyj --convert aby konwertować zwykły Markdown[/dim]",
    title="🔄 Converter",
    border_style="blue"
))
```

```bash markpact:run
python demo.py
```
