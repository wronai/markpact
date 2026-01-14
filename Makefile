.PHONY: help extract run clean install dev test test-cov lint format build publish publish-test convert bump-patch bump-minor bump-major version

PYTHON ?= python3
README ?= README.md
SANDBOX ?= ./sandbox

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

extract: ## Extract bootstrap from README to markpact.py
	sed -n '/^```markpact:bootstrap/,/^```[[:space:]]*$$/p' $(README) | sed '1d;$$d' > markpact.py
	@echo "Extracted markpact.py"

run: extract ## Run markpact bootstrap
	$(PYTHON) markpact.py $(README)

run-port: extract ## Run with custom port (usage: make run-port PORT=8001)
	MARKPACT_PORT=$(PORT) $(PYTHON) markpact.py $(README)

run-cli: ## Run using installed CLI (usage: make run-cli README=path/to/README.md)
	markpact $(README)

convert: ## Convert regular Markdown to markpact (usage: make convert README=path/to/file.md)
	markpact $(README) --convert-only

clean: ## Remove sandbox, build artifacts, and generated files
	rm -rf $(SANDBOX) markpact.py dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned all generated files"

install: ## Install markpact package
	$(PYTHON) -m pip install -e .

dev: ## Install dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest tests/ -v --cov=src/markpact --cov-report=term-missing

lint: ## Run linter
	$(PYTHON) -m ruff check src/ tests/

format: ## Format code
	$(PYTHON) -m ruff format src/ tests/

build: clean ## Build package
	$(PYTHON) -m build

publish-test: build ## Publish to TestPyPI (uses ~/.pypirc credentials)
	$(PYTHON) -m twine upload --repository testpypi --config-file ~/.pypirc dist/*

publish: bump-patch build ## Publish to PyPI production (uses ~/.pypirc credentials)
	$(PYTHON) -m twine upload dist/*

# Version management
version: ## Show current version
	@grep -m1 'version = ' pyproject.toml | cut -d'"' -f2

bump-patch: ## Bump patch version (0.1.0 → 0.1.1)
	bump2version patch --config-file .bumpversion.toml --allow-dirty
	@echo "Bumped to $$(grep -m1 'version = ' pyproject.toml | cut -d'\"' -f2)"

bump-minor: ## Bump minor version (0.1.0 → 0.2.0)
	bump2version minor --config-file .bumpversion.toml --allow-dirty
	@echo "Bumped to $$(grep -m1 'version = ' pyproject.toml | cut -d'\"' -f2)"

bump-major: ## Bump major version (0.1.0 → 1.0.0)
	bump2version major --config-file .bumpversion.toml --allow-dirty
	@echo "Bumped to $$(grep -m1 'version = ' pyproject.toml | cut -d'\"' -f2)"

release: bump-patch publish ## Bump patch and publish
