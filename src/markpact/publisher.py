"""Multi-registry publisher for markpact projects"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .sandbox import Sandbox


@dataclass
class PublishConfig:
    """Configuration for publishing"""
    registry: str  # pypi, npm, docker, github
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    repository: str = ""
    keywords: list[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class PublishResult:
    """Result of a publish operation"""
    success: bool
    registry: str
    message: str
    version: str = ""
    url: str = ""


def _slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "my-project"


def _first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "My Project"


def _first_paragraph(markdown: str) -> str:
    lines = markdown.splitlines()
    started = False
    buf: list[str] = []
    for line in lines:
        if line.startswith("# "):
            started = True
            continue
        if not started:
            continue
        if line.strip() == "":
            if buf:
                break
            continue
        if line.startswith("## "):
            break
        buf.append(line.strip())
    return " ".join(buf).strip()


def _format_subprocess_failure(result: subprocess.CompletedProcess) -> str:
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    payload = stderr or stdout
    if not payload:
        return f"Command failed with exit code {result.returncode}"
    return payload[:400]


def infer_publish_config(
    readme_path: Path,
    markdown: str,
    blocks: list[object],
    run_command: str | None,
) -> "PublishConfig":
    """Infer a reasonable PublishConfig for READMEs without markpact:publish.

    Heuristics:
    - If package.json exists or there are JS/TS file blocks -> npm
    - If Dockerfile exists or run command indicates a web service -> docker
    - If pyproject/setup.py exists -> pypi
    """
    title = _first_heading(markdown)
    description = _first_paragraph(markdown)

    has_package_json = False
    has_pyproject = False
    has_dockerfile = False
    has_js = False
    has_python_pkg = False

    # blocks are markpact.parser.Block, but keep it loose to avoid import cycles
    for b in blocks:
        kind = getattr(b, "kind", "")
        path = getattr(b, "get_path", lambda: None)()
        if kind == "file" and path:
            lower = path.lower()
            if lower.endswith("package.json"):
                has_package_json = True
            if lower.endswith("pyproject.toml") or lower.endswith("setup.py"):
                has_pyproject = True
            if lower.endswith("dockerfile"):
                has_dockerfile = True
            if lower.endswith((".js", ".ts", ".mjs", ".cjs")):
                has_js = True
            if lower.endswith("__init__.py"):
                has_python_pkg = True

    if has_package_json or has_js:
        registry = "npm"
    elif has_dockerfile or (run_command and any(x in run_command for x in ["uvicorn", "gunicorn", "flask run", "node ", "npm start"])):
        registry = "docker"
    elif has_pyproject or has_python_pkg:
        registry = "pypi"
    else:
        registry = "unknown"

    base_name = _slugify(title)
    # Try to make name more unique to avoid PyPI collisions
    if not base_name.startswith("markpact-"):
        base_name = f"markpact-{base_name}"
    default_author = os.environ.get("MARKPACT_AUTHOR") or os.environ.get("GIT_AUTHOR_NAME") or os.environ.get("USER") or ""

    # Reasonable defaults per registry
    if registry == "docker":
        docker_ns = os.environ.get("MARKPACT_DOCKER_NAMESPACE") or os.environ.get("DOCKER_USERNAME") or ""
        name = f"{docker_ns}/{base_name}".strip("/") if docker_ns else base_name
    elif registry == "npm":
        npm_scope = os.environ.get("MARKPACT_NPM_SCOPE") or ""
        name = f"@{npm_scope}/{base_name}" if npm_scope else base_name
    else:
        name = base_name

    version = os.environ.get("MARKPACT_VERSION") or "0.1.0"

    return PublishConfig(
        registry=registry,
        name=name,
        version=version,
        description=description,
        author=default_author,
        license=os.environ.get("MARKPACT_LICENSE", "MIT"),
        repository=os.environ.get("MARKPACT_REPOSITORY", ""),
        keywords=[],
    )


def prompt_publish_config(config: "PublishConfig") -> "PublishConfig":
    """Interactively ask user for missing or important publish fields."""
    print("[markpact] No markpact:publish block found. Let's create one interactively.")
    print("[markpact] Press Enter to accept defaults.")

    def ask(label: str, current: str) -> str:
        value = input(f"{label} [{current}]: ").strip()
        return value or current

    config.registry = ask("Registry (pypi, pypi-test, npm, docker, github, ghcr)", config.registry)
    config.name = ask("Package/Image name", config.name)
    config.version = ask("Version", config.version)
    config.description = ask("Description", config.description)
    config.author = ask("Author", config.author)
    config.license = ask("License", config.license)
    config.repository = ask("Repository URL", config.repository)
    kw = ask("Keywords (comma-separated)", ",".join(config.keywords) if config.keywords else "")
    config.keywords = [k.strip() for k in kw.split(",") if k.strip()]
    return config


def ensure_publish_block_in_readme(readme_path: Path, config: "PublishConfig") -> None:
    """Insert a markpact:publish block into README if none exists."""
    text = readme_path.read_text()
    if "```markpact:publish" in text:
        return

    lines: list[str] = [
        "```markpact:publish\n",
        f"registry = {config.registry}\n",
        f"name = {config.name}\n",
        f"version = {config.version}\n",
        f"description = {config.description}\n",
        f"author = {config.author}\n",
        f"license = {config.license}\n",
    ]
    if config.repository:
        lines.append(f"repository = {config.repository}\n")
    if config.keywords:
        lines.append(f"keywords = {', '.join(config.keywords)}\n")
    lines.append("```\n\n")

    block = "".join(lines)

    # Insert before first markpact:deps if possible
    m = re.search(r"^```markpact:deps\b", text, re.MULTILINE)
    if m:
        new_text = text[: m.start()] + block + text[m.start() :]
    else:
        new_text = text.rstrip() + "\n\n" + block
    readme_path.write_text(new_text)


def generate_publish_config_with_llm(markdown: str, verbose: bool = False) -> Optional["PublishConfig"]:
    """Try to generate a publish config using LLM.

    Requires optional dependency markpact[llm].
    """
    try:
        from .generator import GeneratorConfig, litellm, LITELLM_AVAILABLE
    except Exception:
        return None

    if not LITELLM_AVAILABLE:
        return None

    cfg = GeneratorConfig.from_env()
    if cfg.api_base:
        litellm.api_base = cfg.api_base
    if cfg.api_key:
        if "openrouter" in cfg.model.lower():
            os.environ["OPENROUTER_API_KEY"] = cfg.api_key
        elif "openai" in cfg.model.lower() or cfg.model.startswith("gpt"):
            os.environ["OPENAI_API_KEY"] = cfg.api_key
        elif "anthropic" in cfg.model.lower() or "claude" in cfg.model.lower():
            os.environ["ANTHROPIC_API_KEY"] = cfg.api_key
        elif "groq" in cfg.model.lower():
            os.environ["GROQ_API_KEY"] = cfg.api_key

    system = (
        "You extract publishing metadata from a README. "
        "Return ONLY a single markpact:publish codeblock. "
        "Choose registry=\"docker\" for web services (uvicorn/gunicorn/flask/node server). "
        "Choose registry=\"pypi\" for Python libraries. "
        "Choose registry=\"npm\" for Node libraries. "
        "Always include: registry, name, version, description, author, license."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": markdown[:12000]},
    ]

    try:
        resp = litellm.completion(
            model=cfg.model,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        content = resp.choices[0].message.content
    except Exception:
        return None

    m = re.search(r"```markpact:publish(?P<meta>[^\n]*)\n(?P<body>.*?)\n```", content, re.DOTALL)
    if not m:
        return None
    meta = (m.group("meta") or "").strip()
    body = (m.group("body") or "").strip()
    try:
        return parse_publish_block(body, meta)
    except Exception:
        return None


def bump_version(version: str, bump_type: str = "patch") -> str:
    """Bump semantic version.
    
    Args:
        version: Current version (e.g., "1.2.3")
        bump_type: Type of bump ("major", "minor", "patch")
        
    Returns:
        New version string
    """
    # Remove 'v' prefix if present
    v = version.lstrip("v")
    
    parts = v.split(".")
    if len(parts) != 3:
        parts = ["0", "0", "0"]
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2].split("-")[0])
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def extract_version_from_readme(readme_path: Path) -> Optional[str]:
    """Extract version from README markpact:publish block."""
    content = readme_path.read_text()
    
    # Look for version in publish block
    match = re.search(r'```markpact:publish[^\n]*\n(.*?)```', content, re.DOTALL)
    if match:
        block = match.group(1)
        version_match = re.search(r'version\s*[=:]\s*["\']?([^"\'\n]+)', block)
        if version_match:
            return version_match.group(1).strip()
    
    # Look for version in pyproject.toml style
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    
    return "0.1.0"


def update_version_in_readme(readme_path: Path, new_version: str) -> bool:
    """Update version in README file."""
    content = readme_path.read_text()
    
    # Update version in publish block
    new_content = re.sub(
        r'(version\s*[=:]\s*["\']?)[\d\.]+(["\']?)',
        f'\\g<1>{new_version}\\g<2>',
        content
    )
    
    if new_content != content:
        readme_path.write_text(new_content)
        return True
    
    return False


# ============================================================================
# PyPI Publisher
# ============================================================================

def generate_pyproject_toml(config, sandbox, base_path=None, verbose=True):
    """Generate pyproject.toml for PyPI publishing."""
    # Determine where to put pyproject.toml
    if base_path is None:
        # For Python packages, check if files are in package subdirectory
        package_dir = sandbox.path / config.name
        base_path = package_dir if package_dir.exists() else sandbox.path
    
    # Always use README content as description (append to config.description if provided)
    description_parts = []
    if config.description:
        description_parts.append(config.description)
    
    readme_path = base_path / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()
        # Remove title lines and code blocks, keep the rest
        lines = readme_content.splitlines()
        in_codeblock = False
        for line in lines:
            stripped = line.strip()
            # Skip empty lines, titles, and code blocks
            if not stripped or stripped.startswith("#") or stripped.startswith("```"):
                if stripped.startswith("```"):
                    in_codeblock = not in_codeblock
                continue
            # Skip content inside code blocks
            if in_codeblock:
                continue
            # Add the line to description
            description_parts.append(stripped)
    
    description = " ".join(description_parts)
    # Truncate if too long (PyPI has limits)
    if len(description) > 500:
        description = description[:497] + "..."
    
    import json
    content = f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{config.name}"
version = "{config.version}"
description = "{description}"
readme = "README.md"
license = "{config.license}"
authors = [{{ name = "{config.author}" }}]
keywords = {json.dumps(config.keywords)}
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
requires-python = ">=3.10"

[project.urls]
Homepage = "{config.repository}"

[project.scripts]
markpact-example-pypi = "markpact_example_pypi.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["markpact_example_pypi"]
'''
    
    path = base_path / "pyproject.toml"
    path.write_text(content)
    return path



def publish_pypi(
    config: PublishConfig,
    sandbox: Sandbox,
    test: bool = False,
    verbose: bool = True,
    source_readme_path: Optional[Path] = None,
) -> PublishResult:
    """Publish package to PyPI."""
    
    if verbose:
        print(f"[markpact] Publishing {config.name} v{config.version} to {'TestPyPI' if test else 'PyPI'}...")

    # Validate package name: PyPI normalizes underscores to hyphens; warn if underscores are present
    if "_" in config.name:
        if verbose:
            print(f"[markpact] NOTE: Package name '{config.name}' contains underscores. PyPI normalizes them to hyphens.")
        # Normalize to hyphens for consistency
        config.name = config.name.replace("_", "-")
        if verbose:
            print(f"[markpact] Normalized name to: {config.name}")
    
    # For Python packages, files should be in the package directory
    package_dir = sandbox.path / config.name
    # Also check with underscores (PyPI normalizes them)
    package_dir_underscores = sandbox.path / config.name.replace("-", "_")
    if verbose:
        print(f"[markpact] DEBUG: package_dir_underscores = {package_dir_underscores}")
        print(f"[markpact] DEBUG: package_dir_underscores.exists() = {package_dir_underscores.exists()}")
    if package_dir.exists() or package_dir_underscores.exists():
        # Files are in package subdirectory (e.g., markpact_example_pypi/)
        base_path = package_dir_underscores if package_dir_underscores.exists() else package_dir
    else:
        # Files are in sandbox root
        base_path = sandbox.path

    # Generate pyproject.toml (always ensure it reflects current config)
    generate_pyproject_toml(config, sandbox, base_path, verbose)

    # Auto-install missing build backend if needed (e.g., hatchling)
    pyproject_path = base_path / "pyproject.toml"
    if pyproject_path.exists():
        build_backend = None
        # Try to parse TOML (Python 3.11+ has tomllib; fallback to tomli or regex)
        try:
            import tomllib
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            build_backend = data.get("build-system", {}).get("build-backend")
        except ImportError:
            try:
                import tomli
                with pyproject_path.open("rb") as f:
                    data = tomli.load(f)
                build_backend = data.get("build-system", {}).get("build-backend")
            except ImportError:
                # Fallback: simple regex for build-backend
                content = pyproject_path.read_text()
                m = re.search(r"build-backend\s*=\s*['\"]([^'\"]+)['\"]", content)
                if m:
                    build_backend = m.group(1)
        except Exception:
            # If TOML parsing fails, fallback to regex
            try:
                content = pyproject_path.read_text()
                m = re.search(r"build-backend\s*=\s*['\"]([^'\"]+)['\"]", content)
                if m:
                    build_backend = m.group(1)
            except Exception:
                pass

        if build_backend == "hatchling.build":
            try:
                import hatchling
            except ImportError:
                if verbose:
                    print("[markpact] Installing missing build backend: hatchling")
                install_result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "hatchling"],
                    capture_output=True,
                    text=True,
                )
                if install_result.returncode != 0 and verbose:
                    print("[markpact] WARNING: Failed to auto-install hatchling:")
                    print(install_result.stderr[-500:] if install_result.stderr else install_result.stdout[-500:])
    
    
    # Copy README.md from source to sandbox if it exists
    if verbose:
        print(f"[markpact] DEBUG: source_readme_path = {source_readme_path}")
        print(f"[markpact] DEBUG: source_readme_path.exists() = {source_readme_path.exists() if source_readme_path else 'None'}")
        print(f"[markpact] DEBUG: base_path = {base_path}")
    if source_readme_path and source_readme_path.exists():
        if verbose:
            print(f"[markpact] Copying README from {source_readme_path}")
            print(f"[markpact] To {base_path / 'README.md'}")
        readme = base_path / "README.md"
        content = source_readme_path.read_text()
        if verbose:
            print(f"[markpact] README content length: {len(content)}")
        readme.write_text(content)
        if verbose:
            print(f"[markpact] README written, exists: {readme.exists()}")
    else:
        if verbose:
            print(f"[markpact] Creating minimal README in sandbox")
        # Create README.md in sandbox if not exists
        readme = base_path / "README.md"
        if not readme.exists():
            readme.write_text(f"# {config.name}\n\n{config.description}\n")
    
    # Build package
    if verbose:
        print("[markpact] Building package...")
    
    build_result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    
    if build_result.returncode != 0:
        if verbose:
            print("[markpact] Build stdout/stderr:")
            print("--- STDOUT ---")
            print(build_result.stdout[-1000:] if build_result.stdout else "(empty)")
            print("--- STDERR ---")
            print(build_result.stderr[-1000:] if build_result.stderr else "(empty)")
            print("--- END ---")
            # Common hint for missing build tool
            if "No module named 'build'" in (build_result.stdout or "") or "No module named 'build'" in (build_result.stderr or ""):
                print("[markpact] HINT: 'build' package not found. Install it with: pip install build")
            elif "Cannot import 'hatchling.build'" in (build_result.stdout or "") or "Backend 'hatchling.build' is not available" in (build_result.stdout or ""):
                print("[markpact] HINT: 'hatchling' backend not found. Install it with: pip install hatchling")
        return PublishResult(
            success=False,
            registry="pypi",
            message=f"Build failed: {_format_subprocess_failure(build_result)}",
            version=config.version,
        )
    
    # Upload to PyPI
    if verbose:
        print("[markpact] Uploading to PyPI...")

    env = os.environ.copy()
    env.setdefault("TWINE_NON_INTERACTIVE", "1")

    token_env = "MARKPACT_TESTPYPI_TOKEN" if test else "MARKPACT_PYPI_TOKEN"
    token = env.get(token_env, "").strip()
    if token:
        env.setdefault("TWINE_USERNAME", "__token__")
        env.setdefault("TWINE_PASSWORD", token)

    # Early hint if no credentials are present
    has_env_creds = bool(env.get("TWINE_USERNAME")) and bool(env.get("TWINE_PASSWORD"))
    pypirc_path = Path.home().joinpath(".pypirc")
    has_pypirc = pypirc_path.exists()

    if has_pypirc and verbose:
        print(f"[markpact] Found ~/.pypirc at: {pypirc_path}")

    # Validate ~/.pypirc format (common issue: indented username/password)
    if has_pypirc:
        try:
            import configparser

            cp = configparser.ConfigParser()
            cp.read(pypirc_path)
            section = "testpypi" if test else "pypi"
            if section not in cp:
                if verbose:
                    print(f"[markpact] NOTE: ~/.pypirc exists but section [{section}] is missing")
            else:
                u = (cp.get(section, "username", fallback="") or "").strip()
                p = (cp.get(section, "password", fallback="") or "").strip()
                if verbose:
                    print(f"[markpact] ~/.pypirc section [{section}] parsed:")
                    print(f"    username = {u}")
                    # Mask password for logs
                    masked = (p[:8] + "...") if len(p) > 8 else ("***" if p else "(empty)")
                    print(f"    password = {masked}")
                if not u or not p:
                    print(
                        f"[markpact] NOTE: ~/.pypirc section [{section}] is missing username/password. "
                        f"Ensure the INI keys are NOT indented (no leading spaces)."
                    )
        except Exception as e:
            if verbose:
                print(f"[markpact] WARNING: Failed to parse ~/.pypirc: {e}")
            # Don't block publishing on parse issues; twine may still handle it
            pass

    if not has_env_creds and not has_pypirc:
        if verbose:
            where = "TestPyPI" if test else "PyPI"
            print(f"[markpact] NOTE: No Twine credentials detected for {where}.")
            print(f"[markpact] TIP: set {token_env}=pypi-... or configure ~/.pypirc")
    
    upload_cmd = [sys.executable, "-m", "twine", "upload"]
    if test:
        upload_cmd.extend(["--repository", "testpypi"])

    # Explicitly pass config file if present (avoids HOME/env edge cases)
    if has_pypirc:
        upload_cmd.extend(["--config-file", str(pypirc_path)])

    # Verbose twine output for diagnostics
    if verbose:
        upload_cmd.append("--verbose")

    upload_cmd.append("dist/*")

    if verbose:
        print(f"[markpact] Running twine command:")
        print(f"    {' '.join(upload_cmd)}")

    upload_result = subprocess.run(
        " ".join(upload_cmd),
        shell=True,
        cwd=base_path,
        capture_output=True,
        text=True,
        env=env,
    )
    
    if upload_result.returncode != 0:
        where = "TestPyPI" if test else "PyPI"
        if verbose:
            print("[markpact] Full twine stdout/stderr for debugging:")
            print("--- STDOUT ---")
            print(upload_result.stdout[-2000:] if upload_result.stdout else "(empty)")
            print("--- STDERR ---")
            print(upload_result.stderr[-2000:] if upload_result.stderr else "(empty)")
            print("--- END ---")

        # Detect common PyPI errors and provide actionable hints
        payload = _format_subprocess_failure(upload_result)
        stdout = (upload_result.stdout or "")
        hint = f"Hint: configure ~/.pypirc or set TWINE_USERNAME/TWINE_PASSWORD (or {token_env}).\nTarget: {where}"
        if "File already exists" in payload or "file-name-reuse" in payload or "File already exists" in stdout:
            hint = (
                f"Hint: a file for this version already exists on {where}. "
                f"Try bumping the version with --bump patch/minor/major or change version in the markpact:publish block."
            )
        elif "too similar to an existing project" in payload or "too similar to an existing project" in stdout:
            hint = (
                f"Hint: the package name is too similar to an existing project on {where}. "
                f"Change the 'name =' in the markpact:publish block to something more unique."
            )

        return PublishResult(
            success=False,
            registry="pypi",
            message=f"Upload failed: {payload}\n{hint}",
            version=config.version,
        )
    
    url = f"https://{'test.' if test else ''}pypi.org/project/{config.name}/"
    return PublishResult(
        success=True,
        registry="pypi",
        message=f"Published to {'TestPyPI' if test else 'PyPI'}",
        version=config.version,
        url=url,
    )


# ============================================================================
# npm Publisher
# ============================================================================

def generate_package_json(config: PublishConfig, sandbox: Sandbox) -> Path:
    """Generate package.json for npm publishing."""
    # Always use README content as description (append to config.description if provided)
    description_parts = []
    if config.description:
        description_parts.append(config.description)
    
    readme_path = sandbox.path / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()
        # Remove title lines and code blocks, keep the rest
        lines = readme_content.splitlines()
        in_codeblock = False
        for line in lines:
            stripped = line.strip()
            # Skip empty lines, titles, and code blocks
            if not stripped or stripped.startswith("#") or stripped.startswith("```"):
                if stripped.startswith("```"):
                    in_codeblock = not in_codeblock
                continue
            # Skip content inside code blocks
            if in_codeblock:
                continue
            # Add the line to description
            description_parts.append(stripped)
    
    description = " ".join(description_parts)
    # Truncate if too long (npm has limits)
    if len(description) > 500:
        description = description[:497] + "..."
    
    package = {
        "name": config.name,
        "version": config.version,
        "description": description,
        "main": "index.js",
        "scripts": {
            "test": "echo \"No tests specified\" && exit 0"
        },
        "keywords": config.keywords,
        "author": config.author,
        "license": config.license,
        "repository": {
            "type": "git",
            "url": config.repository
        } if config.repository else {}
    }
    
    path = sandbox.path / "package.json"
    path.write_text(json.dumps(package, indent=2))
    return path


def publish_npm(
    config: PublishConfig,
    sandbox: Sandbox,
    registry: str = "https://registry.npmjs.org",
    verbose: bool = True,
) -> PublishResult:
    """Publish package to npm registry."""
    
    if verbose:
        print(f"[markpact] Publishing {config.name} v{config.version} to npm...")
    
    # Generate package.json if not exists
    package_json = sandbox.path / "package.json"
    if not package_json.exists():
        generate_package_json(config, sandbox)
    
    # Create index.js if not exists
    index_js = sandbox.path / "index.js"
    if not index_js.exists():
        index_js.write_text(f'module.exports = {{ name: "{config.name}", version: "{config.version}" }};\n')
    
    # Publish
    cmd = ["npm", "publish", "--access", "public"]
    if registry != "https://registry.npmjs.org":
        cmd.extend(["--registry", registry])
    
    result = subprocess.run(
        cmd,
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return PublishResult(
            success=False,
            registry="npm",
            message=f"Publish failed: {_format_subprocess_failure(result)}\nHint: run npm login and ensure package name is valid",
            version=config.version,
        )
    
    return PublishResult(
        success=True,
        registry="npm",
        message="Published to npm",
        version=config.version,
        url=f"https://www.npmjs.com/package/{config.name}",
    )


# ============================================================================
# Docker Publisher
# ============================================================================

def generate_dockerfile(config: PublishConfig, sandbox: Sandbox, base_image: str = "python:3.12-slim") -> Path:
    """Generate Dockerfile for Docker publishing."""
    # Always use README content as description (append to config.description if provided)
    description_parts = []
    if config.description:
        description_parts.append(config.description)
    
    readme_path = sandbox.path / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()
        # Remove title lines and code blocks, keep the rest
        lines = readme_content.splitlines()
        in_codeblock = False
        for line in lines:
            stripped = line.strip()
            # Skip empty lines, titles, and code blocks
            if not stripped or stripped.startswith("#") or stripped.startswith("```"):
                if stripped.startswith("```"):
                    in_codeblock = not in_codeblock
                continue
            # Skip content inside code blocks
            if in_codeblock:
                continue
            # Add the line to description
            description_parts.append(stripped)
    
    description = " ".join(description_parts)
    # Truncate if too long (Docker labels have limits)
    if len(description) > 500:
        description = description[:497] + "..."
    
    content = f'''FROM {base_image}

LABEL maintainer="{config.author}"
LABEL version="{config.version}"
LABEL description="{description}"

WORKDIR /app

COPY . .

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

CMD ["python", "-m", "http.server", "8000"]
'''
    
    path = sandbox.path / "Dockerfile"
    path.write_text(content)
    return path


def publish_docker(
    config: PublishConfig,
    sandbox: Sandbox,
    registry: str = "docker.io",
    tag: Optional[str] = None,
    verbose: bool = True,
) -> PublishResult:
    """Build and push Docker image to registry."""
    
    image_name = f"{registry}/{config.name}" if registry != "docker.io" else config.name
    image_tag = tag or config.version
    full_image = f"{image_name}:{image_tag}"
    
    if verbose:
        print(f"[markpact] Building Docker image: {full_image}...")
    
    # Generate Dockerfile if not exists
    dockerfile = sandbox.path / "Dockerfile"
    if not dockerfile.exists():
        generate_dockerfile(config, sandbox)
    
    # Build image
    build_result = subprocess.run(
        ["docker", "build", "-t", full_image, "-t", f"{image_name}:latest", "."],
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    
    if build_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="docker",
            message=f"Build failed: {_format_subprocess_failure(build_result)}",
            version=config.version,
        )
    
    if verbose:
        print(f"[markpact] Pushing to {registry}...")
    
    # Push image
    push_result = subprocess.run(
        ["docker", "push", full_image],
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    
    if push_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="docker",
            message=f"Push failed: {_format_subprocess_failure(push_result)}\nHint: docker login and ensure repository exists",
            version=config.version,
        )
    
    # Also push latest
    subprocess.run(
        ["docker", "push", f"{image_name}:latest"],
        cwd=base_path,
        capture_output=True,
    )
    
    return PublishResult(
        success=True,
        registry="docker",
        message=f"Pushed to {registry}",
        version=config.version,
        url=f"https://hub.docker.com/r/{config.name}" if registry == "docker.io" else f"{registry}/{config.name}",
    )


# ============================================================================
# GitHub Packages Publisher
# ============================================================================

def publish_github_packages(
    config: PublishConfig,
    sandbox: Sandbox,
    package_type: str = "npm",  # npm, docker, maven, nuget
    verbose: bool = True,
) -> PublishResult:
    """Publish to GitHub Packages."""
    
    if package_type == "npm":
        return publish_npm(
            config, sandbox,
            registry="https://npm.pkg.github.com",
            verbose=verbose,
        )
    elif package_type == "docker":
        return publish_docker(
            config, sandbox,
            registry="ghcr.io",
            verbose=verbose,
        )
    else:
        return PublishResult(
            success=False,
            registry="github",
            message=f"Unsupported package type: {package_type}",
            version=config.version,
        )


# ============================================================================
# Main publish function
# ============================================================================

def parse_publish_block(block_body: str, meta: str = "") -> PublishConfig:
    """Parse publish block content into config.
    
    Args:
        block_body: The body of the publish block
        meta: The meta line (first line after markpact:publish)
    """
    config = {
        "registry": "pypi",
        "name": "my-package",
        "version": "0.1.0",
        "description": "",
        "author": "",
        "license": "MIT",
        "repository": "",
        "keywords": [],
    }
    
    # Include meta in parsing if it contains config
    all_lines = []
    if meta and "=" in meta:
        all_lines.append(meta)
    all_lines.extend(block_body.strip().splitlines())
    
    for line in all_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        if "=" in line:
            key, _, value = line.partition("=")
        elif ":" in line:
            key, _, value = line.partition(":")
        else:
            continue
        
        key = key.strip().lower()
        value = value.strip().strip('"\'')
        
        if key in config:
            if key == "keywords":
                config[key] = [k.strip() for k in value.split(",")]
            else:
                config[key] = value
    
    return PublishConfig(**config)


def publish(
    config: PublishConfig,
    sandbox: Sandbox,
    bump: Optional[str] = None,
    verbose: bool = True,
    source_readme_path: Optional[Path] = None,
) -> PublishResult:
    """Publish to specified registry.
    
    Args:
        config: Publish configuration
        sandbox: Sandbox with files to publish
        bump: Version bump type ("major", "minor", "patch") or None
        verbose: Print progress
        
    Returns:
        PublishResult
    """
    # Bump version if requested
    if bump:
        config.version = bump_version(config.version, bump)
        if verbose:
            print(f"[markpact] Bumped version to {config.version}")
    
    # Dispatch to appropriate publisher
    if config.registry == "pypi":
        return publish_pypi(config, sandbox, verbose=verbose, source_readme_path=source_readme_path)
    elif config.registry == "pypi-test":
        return publish_pypi(config, sandbox, test=True, verbose=verbose, source_readme_path=source_readme_path)
    elif config.registry == "npm":
        return publish_npm(config, sandbox, verbose=verbose)
    elif config.registry == "docker":
        return publish_docker(config, sandbox, verbose=verbose)
    elif config.registry == "github":
        return publish_github_packages(config, sandbox, verbose=verbose)
    elif config.registry == "ghcr":
        return publish_docker(config, sandbox, registry="ghcr.io", verbose=verbose)
    else:
        return PublishResult(
            success=False,
            registry=config.registry,
            message=f"Unknown registry: {config.registry}",
            version=config.version,
        )
