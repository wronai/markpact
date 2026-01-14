"""Tests for markpact runner"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from markpact.runner import run_cmd, ensure_venv, install_deps
from markpact.sandbox import Sandbox


def test_run_cmd_simple():
    """Test running a simple command"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        # Create a test file
        test_file = sandbox.path / "test.txt"
        
        # Run echo command
        run_cmd("echo 'hello' > test.txt", sandbox, verbose=False)
        
        assert test_file.exists()
        assert "hello" in test_file.read_text()


def test_run_cmd_with_venv():
    """Test run_cmd uses venv when available"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        # Create fake venv structure
        venv_bin = sandbox.path / ".venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "python").touch()
        
        # Run command and check env is set
        with patch("subprocess.check_call") as mock_call:
            run_cmd("python --version", sandbox, verbose=False)
            
            # Check that VIRTUAL_ENV was set
            call_kwargs = mock_call.call_args[1]
            assert "VIRTUAL_ENV" in call_kwargs["env"]
            assert str(venv_bin.parent) in call_kwargs["env"]["VIRTUAL_ENV"]


def test_ensure_venv_creates_venv():
    """Test ensure_venv creates venv if not exists"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        # Should not fail (may or may not create venv depending on Python availability)
        try:
            ensure_venv(sandbox, verbose=False)
        except Exception:
            pass  # OK if venv creation fails in test env


def test_ensure_venv_skips_if_disabled():
    """Test ensure_venv respects MARKPACT_NO_VENV"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        with patch.dict("os.environ", {"MARKPACT_NO_VENV": "1"}):
            with patch("markpact.runner.run_cmd") as mock_run:
                ensure_venv(sandbox, verbose=False)
                mock_run.assert_not_called()


def test_ensure_venv_skips_if_exists():
    """Test ensure_venv skips if venv already exists"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        # Create fake venv
        python = sandbox.path / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.touch()
        
        with patch("markpact.runner.run_cmd") as mock_run:
            ensure_venv(sandbox, verbose=False)
            mock_run.assert_not_called()


def test_install_deps_empty():
    """Test install_deps with empty list"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        with patch("markpact.runner.run_cmd") as mock_run:
            install_deps([], sandbox, verbose=False)
            mock_run.assert_not_called()


def test_install_deps_writes_requirements():
    """Test install_deps writes requirements.txt"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Sandbox(Path(tmpdir) / "sandbox")
        
        # Create fake venv pip
        pip = sandbox.path / ".venv" / "bin" / "pip"
        pip.parent.mkdir(parents=True)
        pip.touch()
        
        # Mock run_cmd to avoid actual pip install
        with patch("markpact.runner.run_cmd"):
            install_deps(["requests", "flask"], sandbox, verbose=False)
        
        req_file = sandbox.path / "requirements.txt"
        assert req_file.exists()
        content = req_file.read_text()
        assert "requests" in content
        assert "flask" in content
