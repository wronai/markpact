"""Tests for markpact sandbox"""

import tempfile
from pathlib import Path

from markpact.sandbox import Sandbox


def test_sandbox_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = Sandbox(Path(tmpdir) / "test_sandbox")
        assert sb.path.exists()


def test_write_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = Sandbox(Path(tmpdir) / "test_sandbox")
        f = sb.write_file("app/main.py", "print('hello')")
        assert f.exists()
        assert f.read_text() == "print('hello')"


def test_write_requirements():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = Sandbox(Path(tmpdir) / "test_sandbox")
        req = sb.write_requirements(["fastapi", "uvicorn"])
        assert req.exists()
        assert "fastapi" in req.read_text()
        assert "uvicorn" in req.read_text()


def test_venv_paths():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = Sandbox(Path(tmpdir) / "test_sandbox")
        assert sb.venv_bin == sb.path / ".venv" / "bin"
        assert sb.venv_pip == sb.path / ".venv" / "bin" / "pip"
        assert not sb.has_venv()


def test_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        sb = Sandbox(Path(tmpdir) / "test_sandbox")
        sb.write_file("test.txt", "hello")
        assert sb.path.exists()
        sb.clean()
        assert not sb.path.exists()
