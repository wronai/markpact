"""Docker sandbox runner for Markpact"""

import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + max_attempts}")


def stop_existing_container(container_name: str, verbose: bool = False) -> bool:
    """Stop and remove existing container if it exists."""
    try:
        result = subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
        )
        if result.returncode == 0 and verbose:
            print(f"[markpact] Removed existing container: {container_name}")
        return result.returncode == 0
    except Exception:
        return False

DOCKERFILE_TEMPLATE = '''FROM python:3.12-slim

WORKDIR /app

# Install dependencies if requirements.txt exists
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Default port
ENV MARKPACT_PORT=8000
EXPOSE ${MARKPACT_PORT}

# Run command will be provided at runtime
CMD ["python", "-m", "http.server", "8000"]
'''


def generate_dockerfile(sandbox_path: Path, deps: list[str], run_command: str) -> Path:
    """Generate a Dockerfile for the markpact project."""
    dockerfile_path = sandbox_path / "Dockerfile"
    
    # Create requirements.txt
    if deps:
        requirements_path = sandbox_path / "requirements.txt"
        requirements_path.write_text("\n".join(deps))
    
    # Determine CMD based on run_command
    if "uvicorn" in run_command:
        cmd = run_command.replace("${MARKPACT_PORT:-8000}", "${MARKPACT_PORT}")
        cmd_parts = cmd.split()
        cmd_json = str(cmd_parts).replace("'", '"')
    else:
        cmd_parts = run_command.strip().split()
        cmd_json = str(cmd_parts).replace("'", '"')
    
    dockerfile_content = f'''FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Default port
ENV MARKPACT_PORT=8000
EXPOSE 8000

CMD {cmd_json}
'''
    
    dockerfile_path.write_text(dockerfile_content)
    return dockerfile_path


def is_port_free(port: int) -> bool:
    """Check if a port is free."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False


def build_and_run_docker(
    sandbox_path: Path,
    image_name: str = "markpact-app",
    port: int = 8000,
    verbose: bool = True,
    auto_find_port: bool = True,
) -> int:
    """Build and run Docker container from sandbox.
    
    Automatically finds a free port if the specified port is in use.
    """
    
    if verbose:
        print(f"[markpact] Building Docker image: {image_name}")
    
    # Build image
    build_result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        cwd=sandbox_path,
        capture_output=not verbose,
    )
    
    if build_result.returncode != 0:
        print(f"[markpact] ERROR: Docker build failed", file=sys.stderr)
        if not verbose:
            print(build_result.stderr.decode(), file=sys.stderr)
        return build_result.returncode
    
    container_name = f"{image_name}-container"
    
    # Stop any existing container with the same name
    stop_existing_container(container_name, verbose=verbose)
    
    # Find a free port if needed
    current_port = port
    if auto_find_port and not is_port_free(port):
        if verbose:
            print(f"[markpact] Port {port} is in use, finding a free port...")
        try:
            current_port = find_free_port(start_port=port + 1)
            if verbose:
                print(f"[markpact] Using port {current_port} instead")
        except RuntimeError as e:
            print(f"[markpact] ERROR: {e}", file=sys.stderr)
            return 1
    
    if verbose:
        print(f"[markpact] Running container on port {current_port}")
        print(f"[markpact] Access at: http://localhost:{current_port}")
        print(f"[markpact] Press Ctrl+C to stop")
    
    # Run container
    try:
        run_result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-p", f"{current_port}:{current_port}",
                "-e", f"MARKPACT_PORT={current_port}",
                "--name", container_name,
                image_name,
            ],
            cwd=sandbox_path,
        )
        return run_result.returncode
    except KeyboardInterrupt:
        print(f"\n[markpact] Stopping container...")
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        return 0


def check_docker_available() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def run_docker_with_logs(
    sandbox_path: Path,
    image_name: str = "markpact-app",
    port: int = 8000,
    follow_logs: bool = True,
    verbose: bool = True,
    auto_find_port: bool = True,
) -> tuple[subprocess.Popen, int]:
    """Start Docker container and return process for log monitoring.
    
    Returns:
        Tuple of (Popen process, actual port used)
    """
    container_name = f"{image_name}-container"
    
    # Stop any existing container
    stop_existing_container(container_name)
    
    # Find free port if needed
    current_port = port
    if auto_find_port and not is_port_free(port):
        if verbose:
            print(f"[markpact] Port {port} is in use, finding a free port...")
        current_port = find_free_port(start_port=port + 1)
    
    if verbose:
        print(f"[markpact] Starting Docker container: {image_name}")
        print(f"[markpact] Port: {current_port}")
    
    process = subprocess.Popen(
        [
            "docker", "run", "--rm",
            "-p", f"{current_port}:{current_port}",
            "-e", f"MARKPACT_PORT={current_port}",
            "--name", container_name,
            image_name,
        ],
        cwd=sandbox_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    
    return process, current_port


def stream_docker_logs(process: subprocess.Popen, timeout: Optional[int] = None):
    """Stream logs from Docker container."""
    import select
    import sys
    
    start_time = time.time() if timeout else None
    
    try:
        while True:
            if timeout and (time.time() - start_time) > timeout:
                break
            
            if process.poll() is not None:
                # Process ended
                break
            
            line = process.stdout.readline()
            if line:
                print(f"[docker] {line.rstrip()}")
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("\n[markpact] Stopping container...")
        subprocess.run(["docker", "stop", f"{process.args[8]}"], capture_output=True)


def run_docker_with_tests(
    sandbox_path: Path,
    test_body: str,
    image_name: str = "markpact-app",
    port: int = 8000,
    verbose: bool = True,
    auto_find_port: bool = True,
) -> tuple[int, "TestSuite"]:
    """Build, run Docker container, execute tests, and return results."""
    from .tester import run_tests_from_block, wait_for_service, TestSuite, TestResult
    
    # Build image first
    if verbose:
        print(f"[markpact] Building Docker image: {image_name}")
    
    build_result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        cwd=sandbox_path,
        capture_output=not verbose,
    )
    
    if build_result.returncode != 0:
        print(f"[markpact] ERROR: Docker build failed")
        return 1, TestSuite([TestResult("Docker build", False, "Build failed", 0)])
    
    # Find free port if needed
    current_port = port
    if auto_find_port and not is_port_free(port):
        if verbose:
            print(f"[markpact] Port {port} is in use, finding a free port...")
        try:
            current_port = find_free_port(start_port=port + 1)
            if verbose:
                print(f"[markpact] Using port {current_port} instead")
        except RuntimeError as e:
            return 1, TestSuite([TestResult("Port allocation", False, str(e), 0)])
    
    # Start container
    container_name = f"{image_name}-test-{current_port}"
    
    # Stop any existing container with same name
    stop_existing_container(container_name)
    
    if verbose:
        print(f"[markpact] Starting container: {container_name}")
    
    process = subprocess.Popen(
        [
            "docker", "run", "--rm",
            "-p", f"{current_port}:{current_port}",
            "-e", f"MARKPACT_PORT={current_port}",
            "--name", container_name,
            image_name,
        ],
        cwd=sandbox_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    
    try:
        # Wait for service
        base_url = f"http://localhost:{current_port}"
        if verbose:
            print(f"[markpact] Waiting for service at {base_url}...")
        
        if not wait_for_service(f"{base_url}/health", timeout=60):
            if not wait_for_service(base_url, timeout=10):
                return 1, TestSuite([TestResult("Docker startup", False, "Container did not start", 0)])
        
        if verbose:
            print(f"[markpact] Container ready. Running tests...")
        
        # Run tests
        suite = run_tests_from_block(test_body, base_url)
        suite.print_summary()
        
        return 0 if suite.failed == 0 else 1, suite
        
    finally:
        # Stop container
        if verbose:
            print(f"[markpact] Stopping container...")
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        process.wait(timeout=10)
