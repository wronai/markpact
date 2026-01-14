"""Test runner for markpact projects"""

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .sandbox import Sandbox


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    passed: bool
    message: str
    duration: float = 0.0


@dataclass  
class TestSuite:
    """Collection of test results"""
    results: list[TestResult]
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)
    
    @property
    def total(self) -> int:
        return len(self.results)
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST RESULTS: {self.passed}/{self.total} passed")
        print(f"{'='*60}")
        for r in self.results:
            status = "✓" if r.passed else "✗"
            print(f"  {status} {r.name}: {r.message}")
        print()


def wait_for_service(url: str, timeout: int = 30, interval: float = 0.5) -> bool:
    """Wait for a service to become available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = Request(url, method='GET')
            with urlopen(req, timeout=5) as resp:
                return True
        except (URLError, HTTPError, TimeoutError, ConnectionRefusedError, OSError):
            time.sleep(interval)
        except Exception:
            time.sleep(interval)
    return False


def http_request(
    method: str,
    url: str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 10,
) -> tuple[int, dict | str]:
    """Make an HTTP request and return (status_code, response_body)."""
    headers = headers or {}
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    else:
        body = None
    
    req = Request(url, data=body, headers=headers, method=method.upper())
    
    try:
        with urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode()
            try:
                return resp.status, json.loads(content)
            except json.JSONDecodeError:
                return resp.status, content
    except HTTPError as e:
        content = e.read().decode()
        try:
            return e.code, json.loads(content)
        except json.JSONDecodeError:
            return e.code, content
    except URLError as e:
        return 0, str(e)


def run_http_test(test_spec: str, base_url: str = "http://localhost:8000") -> TestResult:
    """Run a single HTTP test from spec.
    
    Format:
        METHOD /path [EXPECT status_code] [BODY json]
        
    Examples:
        GET /health EXPECT 200
        POST /shorten BODY {"url": "https://example.com"} EXPECT 200
        GET /abc123 EXPECT 302
    """
    start = time.time()
    
    # Parse test spec
    parts = test_spec.strip().split()
    if len(parts) < 2:
        return TestResult(test_spec, False, "Invalid test format", 0)
    
    method = parts[0].upper()
    path = parts[1]
    url = f"{base_url.rstrip('/')}{path}"
    
    expected_status = None
    body = None
    
    # Parse EXPECT and BODY
    spec_rest = " ".join(parts[2:])
    
    expect_match = re.search(r'EXPECT\s+(\d+)', spec_rest)
    if expect_match:
        expected_status = int(expect_match.group(1))
    
    body_match = re.search(r'BODY\s+(\{.*\})', spec_rest)
    if body_match:
        try:
            body = json.loads(body_match.group(1))
        except json.JSONDecodeError:
            return TestResult(test_spec, False, "Invalid JSON body", 0)
    
    # Execute request
    status, response = http_request(method, url, data=body)
    duration = time.time() - start
    
    # Check result
    if expected_status is not None:
        if status == expected_status:
            return TestResult(
                f"{method} {path}",
                True,
                f"Status {status} (expected {expected_status})",
                duration
            )
        else:
            return TestResult(
                f"{method} {path}",
                False,
                f"Status {status} (expected {expected_status})",
                duration
            )
    else:
        # No expectation, just check for successful response
        if 200 <= status < 400:
            return TestResult(f"{method} {path}", True, f"Status {status}", duration)
        else:
            return TestResult(f"{method} {path}", False, f"Status {status}", duration)


def run_tests_from_block(test_body: str, base_url: str = "http://localhost:8000") -> TestSuite:
    """Run all tests defined in a test block."""
    results = []
    
    for line in test_body.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        result = run_http_test(line, base_url)
        results.append(result)
    
    return TestSuite(results)


def run_service_with_tests(
    run_command: str,
    test_body: str,
    sandbox: Sandbox,
    port: int = 8000,
    verbose: bool = True,
) -> tuple[int, TestSuite]:
    """Start a service, run tests, and return results.
    
    Returns:
        Tuple of (exit_code, test_suite)
    """
    base_url = f"http://localhost:{port}"
    
    # Prepare environment
    env = os.environ.copy()
    env["MARKPACT_PORT"] = str(port)
    if sandbox.venv_bin.exists():
        env["VIRTUAL_ENV"] = str(sandbox.venv_bin.parent)
        env["PATH"] = f"{sandbox.venv_bin}:{env.get('PATH', '')}"
    
    # Start service in background
    if verbose:
        print(f"[markpact] Starting service on port {port}...")
    
    # Replace port variable in command
    cmd = run_command.replace("${MARKPACT_PORT:-8000}", str(port))
    cmd = re.sub(r'--port\s+\d+', f'--port {port}', cmd)
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=sandbox.path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    
    try:
        # Give the process a moment to start
        time.sleep(2)
        
        # Check if process crashed immediately
        if process.poll() is not None:
            output = process.stdout.read().decode() if process.stdout else ""
            return 1, TestSuite([TestResult("Service startup", False, f"Process exited: {output[:200]}", 0)])
        
        # Wait for service to start
        if verbose:
            print(f"[markpact] Waiting for service at {base_url}...")
        
        # Try health endpoint first, then root
        if not wait_for_service(f"{base_url}/health", timeout=15):
            if not wait_for_service(f"{base_url}/", timeout=10):
                output = ""
                try:
                    process.terminate()
                    output = process.stdout.read().decode() if process.stdout else ""
                except:
                    pass
                return 1, TestSuite([TestResult("Service startup", False, f"Service did not respond. Output: {output[:200]}", 0)])
        
        if verbose:
            print(f"[markpact] Service ready. Running tests...")
        
        # Run tests
        suite = run_tests_from_block(test_body, base_url)
        suite.print_summary()
        
        return 0 if suite.failed == 0 else 1, suite
        
    finally:
        # Stop service
        if verbose:
            print(f"[markpact] Stopping service...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def run_shell_tests(test_body: str, sandbox: Sandbox, verbose: bool = True) -> TestSuite:
    """Run shell command tests."""
    results = []
    
    env = os.environ.copy()
    if sandbox.venv_bin.exists():
        env["VIRTUAL_ENV"] = str(sandbox.venv_bin.parent)
        env["PATH"] = f"{sandbox.venv_bin}:{env.get('PATH', '')}"
    
    for line in test_body.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        start = time.time()
        
        try:
            result = subprocess.run(
                line,
                shell=True,
                cwd=sandbox.path,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                results.append(TestResult(line[:50], True, "Passed", duration))
            else:
                results.append(TestResult(line[:50], False, f"Exit code {result.returncode}", duration))
                
        except subprocess.TimeoutExpired:
            results.append(TestResult(line[:50], False, "Timeout", time.time() - start))
        except Exception as e:
            results.append(TestResult(line[:50], False, str(e), time.time() - start))
    
    return TestSuite(results)
