.PHONY: help extract run clean install dev test lint format

PYTHON ?= python3
README ?= README.md
SANDBOX ?= ./sandbox

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

extract: ## Extract bootstrap from README to markpact_bootstrap.py
	sed -n '/^```markpact:bootstrap/,/^```[[:space:]]*$$/p' $(README) | sed '1d;$$d' > markpact_bootstrap.py
	@echo "Extracted markpact_bootstrap.py"

run: extract ## Run markpact bootstrap
	$(PYTHON) markpact_bootstrap.py $(README)

run-port: extract ## Run with custom port (usage: make run-port PORT=8001)
	MARKPACT_PORT=$(PORT) $(PYTHON) markpact_bootstrap.py $(README)

clean: ## Remove sandbox and generated files
	rm -rf $(SANDBOX) markpact_bootstrap.py
	@echo "Cleaned sandbox and bootstrap"

install: ## Install markpact package
	$(PYTHON) -m pip install -e .

dev: ## Install dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

lint: ## Run linter
	$(PYTHON) -m ruff check src/ tests/

format: ## Format code
	$(PYTHON) -m ruff format src/ tests/

build: ## Build package
	$(PYTHON) -m build

publish: build ## Publish to PyPI (test)
	$(PYTHON) -m twine upload --repository testpypi dist/*
