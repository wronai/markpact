"""Tests for notebook_converter module."""

import json
import pytest
from pathlib import Path

from markpact.notebook_converter import (
    detect_format,
    parse_jupyter,
    parse_rmarkdown,
    parse_quarto,
    extract_dependencies,
    suggest_run_command,
    notebook_to_markpact,
    convert_notebook,
    get_supported_formats,
    Notebook,
    NotebookCell,
)


def test_detect_format_jupyter():
    """Test detection of Jupyter notebook format."""
    assert detect_format(Path("test.ipynb")) == "jupyter"


def test_detect_format_rmarkdown():
    """Test detection of R Markdown format."""
    assert detect_format(Path("test.Rmd")) == "rmarkdown"
    assert detect_format(Path("test.rmd")) == "rmarkdown"


def test_detect_format_quarto():
    """Test detection of Quarto format."""
    assert detect_format(Path("test.qmd")) == "quarto"


def test_detect_format_unknown():
    """Test detection of unknown format."""
    assert detect_format(Path("test.txt")) is None
    assert detect_format(Path("test.py")) is None


def test_get_supported_formats():
    """Test getting list of supported formats."""
    formats = get_supported_formats()
    assert ".ipynb" in formats
    assert ".rmd" in formats
    assert ".qmd" in formats
    assert len(formats) >= 5


def test_parse_jupyter(tmp_path: Path):
    """Test parsing Jupyter notebook."""
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Test Notebook\n", "Description here."]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["import pandas as pd\n", "df = pd.DataFrame()"],
                "outputs": []
            }
        ],
        "metadata": {
            "kernelspec": {
                "language": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    notebook_path = tmp_path / "test.ipynb"
    notebook_path.write_text(json.dumps(notebook_content))
    
    notebook = parse_jupyter(notebook_path)
    
    assert notebook.title == "Test Notebook"
    assert notebook.language == "python"
    assert len(notebook.cells) == 2
    assert notebook.cells[0].cell_type == "markdown"
    assert notebook.cells[1].cell_type == "code"


def test_extract_dependencies():
    """Test extracting dependencies from notebook."""
    cells = [
        NotebookCell(
            cell_type="code",
            source="import pandas as pd\nimport numpy as np\nfrom fastapi import FastAPI",
            language="python"
        ),
        NotebookCell(
            cell_type="code",
            source="import os\nimport sys",  # stdlib - should be excluded
            language="python"
        )
    ]
    notebook = Notebook(cells=cells, language="python", title="Test")
    
    deps = extract_dependencies(notebook)
    
    assert "pandas" in deps
    assert "numpy" in deps
    assert "fastapi" in deps
    assert "os" not in deps
    assert "sys" not in deps


def test_suggest_run_command_fastapi():
    """Test run command suggestion for FastAPI."""
    cells = [
        NotebookCell(
            cell_type="code",
            source="from fastapi import FastAPI\napp = FastAPI()",
            language="python"
        )
    ]
    notebook = Notebook(cells=cells, language="python", title="Test")
    
    cmd = suggest_run_command(notebook)
    
    assert "uvicorn" in cmd
    assert "8000" in cmd


def test_suggest_run_command_streamlit():
    """Test run command suggestion for Streamlit."""
    cells = [
        NotebookCell(
            cell_type="code",
            source="import streamlit as st\nst.title('Hello')",
            language="python"
        )
    ]
    notebook = Notebook(cells=cells, language="python", title="Test")
    
    cmd = suggest_run_command(notebook)
    
    assert "streamlit" in cmd
    assert "8501" in cmd


def test_suggest_run_command_flask():
    """Test run command suggestion for Flask."""
    cells = [
        NotebookCell(
            cell_type="code",
            source="from flask import Flask\napp = Flask(__name__)",
            language="python"
        )
    ]
    notebook = Notebook(cells=cells, language="python", title="Test")
    
    cmd = suggest_run_command(notebook)
    
    assert "flask" in cmd
    assert "5000" in cmd


def test_notebook_to_markpact():
    """Test converting notebook to markpact format."""
    cells = [
        NotebookCell(
            cell_type="markdown",
            source="# My API\n\nThis is a test API.",
            language="markdown"
        ),
        NotebookCell(
            cell_type="code",
            source="from fastapi import FastAPI\napp = FastAPI()",
            language="python"
        )
    ]
    notebook = Notebook(
        cells=cells,
        language="python",
        title="My API",
        description="This is a test API."
    )
    
    result = notebook_to_markpact(notebook, verbose=False)
    
    assert "# My API" in result
    assert "```text markpact:deps python" in result
    assert "```python markpact:file path=" in result
    assert "```bash markpact:run" in result
    assert "fastapi" in result


def test_convert_notebook_jupyter(tmp_path: Path):
    """Test full conversion of Jupyter notebook."""
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Sample API"]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["from fastapi import FastAPI\napp = FastAPI()"],
                "outputs": []
            }
        ],
        "metadata": {
            "kernelspec": {"language": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    notebook_path = tmp_path / "sample.ipynb"
    notebook_path.write_text(json.dumps(notebook_content))
    
    output_path = tmp_path / "README.md"
    
    result = convert_notebook(notebook_path, output_path, verbose=False)
    
    assert output_path.exists()
    assert "# Sample API" in result
    assert "markpact:deps" in result
    assert "markpact:file" in result
    assert "markpact:run" in result


def test_convert_notebook_file_not_found():
    """Test error handling for missing notebook file."""
    with pytest.raises(FileNotFoundError):
        convert_notebook(Path("nonexistent.ipynb"))


def test_convert_notebook_unsupported_format(tmp_path: Path):
    """Test error handling for unsupported format."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")
    
    with pytest.raises(ValueError, match="Unsupported"):
        convert_notebook(txt_file)
