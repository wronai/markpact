# Publikacja pakietu

## Konfiguracja ~/.pypirc

Aby `twine` nie pytał o token przy każdym `make publish`, utwórz plik `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-XXXXXX...

[testpypi]
username = __token__
password = pypi-XXXXXX...
```

### Gdzie wziąć token?

1. **TestPyPI**: https://test.pypi.org/manage/account/token/
2. **PyPI**: https://pypi.org/manage/account/token/

### Uprawnienia pliku

```bash
chmod 600 ~/.pypirc
```

## Komendy Makefile

```bash
# Buduj pakiet
make build

# Publikuj na TestPyPI
make publish

# Publikuj na PyPI produkcyjne
make publish-prod
```

## Ręczna publikacja

Jeśli wolisz nie używać `~/.pypirc`:

```bash
# Buduj
python3 -m build

# Publikuj z tokenem w zmiennej środowiskowej
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-XXXX python3 -m twine upload dist/*
```

## Weryfikacja

```bash
# Sprawdź pakiet na TestPyPI
pip install --index-url https://test.pypi.org/simple/ markpact

# Sprawdź pakiet na PyPI
pip install markpact
```

## Wersjonowanie

Wersja jest zdefiniowana w:
- `src/markpact/__init__.py` (`__version__`)
- `pyproject.toml` (`version`)

Przed publikacją upewnij się, że obie są spójne.

## Troubleshooting

### "Enter your API token" prompt

Twine nie znalazł tokenu. Sprawdź:
1. Czy `~/.pypirc` istnieje
2. Czy ma prawidłowy format (sekcje `[pypi]` / `[testpypi]`)
3. Czy `password` zaczyna się od `pypi-`

### "This environment is not supported for trusted publishing"

To ostrzeżenie jest OK – trusted publishing dotyczy GitHub Actions. 
Lokalna publikacja używa tokenu z `~/.pypirc`.

### "File already exists"

Wersja już istnieje na PyPI. Zwiększ wersję w `pyproject.toml` i `__init__.py`.
