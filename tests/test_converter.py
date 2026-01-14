"""Tests for markpact converter"""

from markpact.converter import (
    convert_markdown_to_markpact,
    detect_block_type,
    suggest_filename,
)


def test_detect_deps_python():
    body = "fastapi\nuvicorn\npydantic"
    tag, meta, conf, reason = detect_block_type("", body)
    assert tag == "deps"
    assert meta == "python"
    assert conf >= 0.8


def test_detect_deps_with_versions():
    body = "requests>=2.28\nflask==2.0.0"
    tag, meta, conf, reason = detect_block_type("", body)
    assert tag == "deps"
    assert meta == "python"


def test_detect_file_python():
    body = "from fastapi import FastAPI\n\napp = FastAPI()"
    tag, meta, conf, reason = detect_block_type("python", body)
    assert tag == "file"
    assert meta == "python"


def test_detect_file_javascript():
    body = "const express = require('express');\nconst app = express();"
    tag, meta, conf, reason = detect_block_type("javascript", body)
    assert tag == "file"
    assert meta == "javascript"


def test_detect_run_command():
    body = "uvicorn app:app --reload --port 8000"
    tag, meta, conf, reason = detect_block_type("bash", body)
    assert tag == "run"


def test_detect_run_python():
    body = "python main.py"
    tag, meta, conf, reason = detect_block_type("bash", body)
    assert tag == "run"


def test_suggest_filename_fastapi():
    body = "from fastapi import FastAPI\napp = FastAPI()"
    name = suggest_filename("python", body, 0)
    assert name == "app.py"


def test_suggest_filename_class():
    body = "class UserService:\n    pass"
    name = suggest_filename("python", body, 0)
    assert name == "userservice.py"


def test_suggest_filename_html():
    body = "<html><head><title>Home</title></head></html>"
    name = suggest_filename("html", body, 0)
    assert "home" in name.lower() or name == "index.html"


def test_convert_simple_markdown():
    md = '''# Test Project

```
fastapi
uvicorn
```

```python
from fastapi import FastAPI
app = FastAPI()
```

```bash
uvicorn app:app
```
'''
    result = convert_markdown_to_markpact(md)
    
    assert not result.has_markpact
    assert len(result.blocks) >= 2  # At least deps and file
    assert "markpact:deps" in result.converted_text or "markpact:file" in result.converted_text


def test_convert_already_markpact():
    md = '''```markpact:deps python
fastapi
```'''
    result = convert_markdown_to_markpact(md)
    
    assert result.has_markpact
    assert len(result.blocks) == 0
    assert result.converted_text == md


def test_convert_preserves_non_code():
    md = '''# Title

Some text here.

```python
print("hello")
```

More text.
'''
    result = convert_markdown_to_markpact(md)
    
    assert "# Title" in result.converted_text
    assert "Some text here." in result.converted_text
    assert "More text." in result.converted_text
