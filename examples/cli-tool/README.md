# CLI Tool – File Organizer

Narzędzie linii poleceń do organizowania plików według rozszerzenia.

## Uruchomienie

```bash
markpact examples/cli-tool/README.md
```

## Użycie

```bash
# Organizuj pliki w bieżącym katalogu
python organizer.py .

# Organizuj pliki w konkretnym katalogu
python organizer.py ~/Downloads

# Podgląd bez przenoszenia
python organizer.py ~/Downloads --dry-run

# Pokaż pomoc
python organizer.py --help
```

## Kategorie

- **images/** – jpg, png, gif, svg, webp
- **documents/** – pdf, doc, docx, txt, md
- **videos/** – mp4, avi, mkv, mov
- **audio/** – mp3, wav, flac, ogg
- **archives/** – zip, tar, gz, rar, 7z
- **code/** – py, js, ts, html, css, json
- **other/** – pozostałe

---

```text markpact:deps python
click
rich
```

```python markpact:file path=organizer.py
#!/usr/bin/env python3
"""File Organizer CLI – organize files by extension."""

import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

CATEGORIES = {
    "images": ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp", "ico"],
    "documents": ["pdf", "doc", "docx", "txt", "md", "rtf", "odt", "xls", "xlsx"],
    "videos": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm"],
    "audio": ["mp3", "wav", "flac", "ogg", "aac", "wma", "m4a"],
    "archives": ["zip", "tar", "gz", "rar", "7z", "bz2", "xz"],
    "code": ["py", "js", "ts", "html", "css", "json", "xml", "yaml", "yml", "sh"],
}

def get_category(extension: str) -> str:
    ext = extension.lower().lstrip(".")
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "other"

@click.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be done")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def organize(directory: str, dry_run: bool, verbose: bool):
    """Organize files in DIRECTORY by extension."""
    
    path = Path(directory)
    files = [f for f in path.iterdir() if f.is_file()]
    
    if not files:
        console.print("[yellow]No files to organize.[/yellow]")
        return
    
    # Count files per category
    stats: dict[str, list[Path]] = {}
    for file in files:
        category = get_category(file.suffix)
        stats.setdefault(category, []).append(file)
    
    # Show table
    table = Table(title=f"📁 Organizing {path}")
    table.add_column("Category", style="cyan")
    table.add_column("Files", style="green")
    table.add_column("Examples", style="dim")
    
    for category, category_files in sorted(stats.items()):
        examples = ", ".join(f.name[:20] for f in category_files[:3])
        if len(category_files) > 3:
            examples += "..."
        table.add_row(category, str(len(category_files)), examples)
    
    console.print(table)
    
    if dry_run:
        console.print("\n[yellow]Dry run – no files moved.[/yellow]")
        return
    
    # Move files
    moved = 0
    for category, category_files in stats.items():
        dest_dir = path / category
        dest_dir.mkdir(exist_ok=True)
        
        for file in category_files:
            dest = dest_dir / file.name
            if dest.exists():
                console.print(f"[yellow]Skip {file.name} (exists)[/yellow]")
                continue
            shutil.move(str(file), str(dest))
            moved += 1
            if verbose:
                console.print(f"[green]✓[/green] {file.name} → {category}/")
    
    console.print(f"\n[green]✓ Moved {moved} files.[/green]")

if __name__ == "__main__":
    organize()
```

```bash markpact:run
python organizer.py --help
```
