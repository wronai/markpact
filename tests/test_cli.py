"""Tests for markpact CLI"""

import tempfile
from pathlib import Path

from markpact.cli import main


def test_cli_help(capsys):
    """Test --help flag"""
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0
    
    captured = capsys.readouterr()
    assert "markpact" in captured.out
    assert "--convert" in captured.out
    assert "--dry-run" in captured.out


def test_cli_version(capsys):
    """Test --version flag"""
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    
    captured = capsys.readouterr()
    from markpact import __version__
    assert __version__ in captured.out


def test_cli_file_not_found(capsys):
    """Test error when file not found"""
    result = main(["nonexistent.md"])
    assert result == 1
    
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_cli_dry_run():
    """Test --dry-run flag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text('''```markpact:deps python
requests
```

```markpact:file python path=app.py
print("hello")
```

```markpact:run python
python app.py
```
''')
        result = main([str(readme), "--dry-run", "-s", f"{tmpdir}/sandbox"])
        assert result == 0


def test_cli_convert_only(capsys):
    """Test --convert-only flag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "sample.md"
        readme.write_text('''# Test

```python
print("hello")
```
''')
        result = main([str(readme), "--convert-only"])
        assert result == 0
        
        captured = capsys.readouterr()
        assert "CONVERSION REPORT" in captured.out


def test_cli_auto_no_markpact(capsys):
    """Test --auto flag with non-markpact file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "sample.md"
        readme.write_text('''# Test

```
requests
flask
```

```python
from flask import Flask
app = Flask(__name__)
```

```bash
flask run
```
''')
        result = main([str(readme), "--auto", "--dry-run", "-s", f"{tmpdir}/sandbox"])
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Converting" in captured.out


def test_cli_save_converted():
    """Test --save-converted flag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "sample.md"
        readme.write_text('''```python
print("hello")
```
''')
        output = Path(tmpdir) / "output.md"
        result = main([str(readme), "--convert-only", "--save-converted", str(output)])
        assert result == 0
        assert output.exists()
        assert "markpact:" in output.read_text()


def test_cli_quiet_mode():
    """Test --quiet flag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text('''```markpact:file python path=test.py
print("test")
```
''')
        result = main([str(readme), "--dry-run", "-q", "-s", f"{tmpdir}/sandbox"])
        assert result == 0
