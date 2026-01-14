# Integracja CI/CD

## GitHub Actions

### Prosty workflow

```yaml
# .github/workflows/markpact.yml
name: Run Markpact

on:
  push:
    branches: [main]
  pull_request:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install markpact
        run: pip install markpact
      
      - name: Run project
        run: markpact README.md --dry-run
```

### Z cache venv

```yaml
name: Run Markpact with Cache

on: [push, pull_request]

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Cache sandbox venv
        uses: actions/cache@v4
        with:
          path: ./sandbox/.venv
          key: ${{ runner.os }}-venv-${{ hashFiles('README.md') }}
      
      - run: pip install markpact
      - run: markpact README.md
```

### Matrix – wiele przykładów

```yaml
name: Test Examples

on: [push]

jobs:
  examples:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        example:
          - fastapi-todo
          - flask-blog
          - cli-tool
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install markpact
      - run: markpact examples/${{ matrix.example }}/README.md --dry-run
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build

markpact:
  stage: build
  image: python:3.12
  script:
    - pip install markpact
    - markpact README.md
  variables:
    MARKPACT_SANDBOX: ./sandbox
    MARKPACT_NO_VENV: "0"
```

## Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY README.md .

RUN pip install markpact && \
    markpact README.md --dry-run

CMD ["markpact", "README.md"]
```

## Wskazówki

### Deterministyczność

Pinuj wersje zależności:

```markdown
```markpact:deps python
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
\```
```

### Bezpieczeństwo

- Traktuj `markpact:run` jak skrypt uruchomieniowy
- W CI uruchamiaj tylko zaufane README
- Rozważ `--dry-run` dla PR z zewnątrz

### Izolacja

```bash
# Każdy job z osobnym sandboxem
MARKPACT_SANDBOX=./sandbox-$CI_JOB_ID markpact README.md
```
