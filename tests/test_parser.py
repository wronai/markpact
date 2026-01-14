"""Tests for markpact parser"""

from markpact.parser import parse_blocks, Block


def test_parse_file_block():
    md = '''```markpact:file python path=app/main.py
print("hello")
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "file"
    assert blocks[0].get_path() == "app/main.py"
    assert blocks[0].body == 'print("hello")'


def test_parse_deps_block():
    md = '''```markpact:deps python
fastapi
uvicorn
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "deps"
    assert "python" in blocks[0].meta
    assert "fastapi" in blocks[0].body


def test_parse_run_block():
    md = '''```markpact:run python
python main.py
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "run"
    assert blocks[0].body == "python main.py"


def test_parse_multiple_blocks():
    md = '''# Test

```markpact:deps python
requests
```

```markpact:file python path=main.py
import requests
```

```markpact:run python
python main.py
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 3
    assert [b.kind for b in blocks] == ["deps", "file", "run"]


def test_empty_meta():
    md = '''```markpact:run
echo hello
```'''
    blocks = parse_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].meta == ""
