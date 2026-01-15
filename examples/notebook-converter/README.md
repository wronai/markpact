# Notebook Converter Example

Przykład konwersji notebooków (.ipynb, .Rmd, .qmd, .dib, .zpln) do formatu markpact.

## Dostępne przykłady

| Plik | Format | Opis |
|------|--------|------|
| `sample.ipynb` | Jupyter Notebook | FastAPI Sample API |
| `sample.Rmd` | R Markdown | Data Analysis API |
| `sample.qmd` | Quarto | Task Manager API |
| `sample.dib` | Databricks | Notes API |
| `sample.zpln` | Zeppelin | Calculator API |

## Obsługiwane formaty

| Format | Rozszerzenie | Opis |
|--------|--------------|------|
| Jupyter Notebook | `.ipynb` | Standard Jupyter, Python/R/Julia |
| R Markdown | `.Rmd` | R z markdown, kompilowane via knitr |
| Quarto | `.qmd` | Wielojęzyczny (R, Python, Julia) |
| Databricks | `.dib` | Python, Scala, R w Databricks |
| Zeppelin | `.zpln` | Python, Scala, SQL, Spark |

## Użycie

```bash
# Lista obsługiwanych formatów
markpact --list-notebook-formats

# Konwersja Jupyter Notebook
markpact --from-notebook sample.ipynb -o project/README.md

# Konwersja i podgląd (bez zapisu)
markpact --from-notebook sample.ipynb --convert-only

# Konwersja i uruchomienie
markpact --from-notebook sample.ipynb -o project/README.md --run

# Konwersja R Markdown
markpact --from-notebook sample.Rmd -o r-project/README.md

# Konwersja Quarto
markpact --from-notebook sample.qmd -o quarto-project/README.md

# Konwersja Zeppelin
markpact --from-notebook sample.zpln -o zeppelin-project/README.md

# Konwersja Databricks
markpact --from-notebook sample.dib -o databricks-project/README.md
```

## Funkcje konwertera

- **Automatyczne wykrywanie zależności** z importów
- **Dodawanie runtime deps** (uvicorn dla FastAPI, gunicorn dla Flask)
- **Łączenie kodu w jeden plik** app.py dla prostoty
- **Sugerowanie komendy run** na podstawie frameworka
- **Zachowanie tytułu i opisu** z pierwszej komórki markdown
