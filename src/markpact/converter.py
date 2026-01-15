"""Markdown to Markpact converter.

Analyzes regular Markdown files and converts code blocks to markpact format
based on heuristics (file paths, package lists, shell commands).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

# Patterns for detecting block types
PATTERNS = {
    "deps_python": [
        r"^(fastapi|flask|django|uvicorn|gunicorn|requests|pandas|numpy|pydantic)",
        r"^[a-z][a-z0-9_-]*[=<>]=?\d",  # package==version
        r"^-r\s+requirements",  # -r requirements.txt
    ],
    "deps_node": [
        r'"(dependencies|devDependencies)":\s*\{',
        r"^(express|react|vue|next|typescript|webpack)",
    ],
    "file_python": [
        r"^(import |from .+ import |def |class |@app\.|@router\.)",
        r"^#!/usr/bin/env python",
    ],
    "file_javascript": [
        r"^(const |let |var |function |import |export |require\()",
        r"^#!/usr/bin/env node",
    ],
    "file_html": [
        r"^<!DOCTYPE|^<html|^<head|^<body",
    ],
    "file_css": [
        r"^(\.|#|@media|@import|body|html)\s*\{",
    ],
    "file_json": [
        r'^\s*\{\s*"',
    ],
    "file_yaml": [
        r"^[a-z_]+:\s*([-\d\"\']|$)",
    ],
    "run": [
        r"^(python|python3|uvicorn|gunicorn|flask|npm|node|streamlit|pytest)",
        r"^(pip install|npm install|yarn)",
    ],
}

# Language to file extension mapping
LANG_EXTENSIONS = {
    "python": ".py",
    "py": ".py",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "html": ".html",
    "css": ".css",
    "json": ".json",
    "yaml": ".yaml",
    "yml": ".yaml",
    "bash": ".sh",
    "sh": ".sh",
    "sql": ".sql",
    "toml": ".toml",
    "ini": ".ini",
}


@dataclass
class ConvertedBlock:
    """A converted markpact block."""
    original_lang: str
    markpact_tag: str
    meta: str
    body: str
    confidence: float
    reason: str


@dataclass
class ConversionResult:
    """Result of converting a Markdown file."""
    original_text: str
    converted_text: str
    blocks: list[ConvertedBlock] = field(default_factory=list)
    has_markpact: bool = False
    changes: list[str] = field(default_factory=list)


def detect_block_type(lang: str, body: str) -> tuple[str, str, float, str]:
    """
    Detect the markpact block type based on language and content.
    
    Returns: (markpact_tag, meta, confidence, reason)
    """
    body_lower = body.lower()
    first_lines = "\n".join(body.split("\n")[:10])
    
    # Check for deps patterns
    for pattern in PATTERNS["deps_python"]:
        if re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
            # Looks like Python dependencies
            if lang in ("", "text", "txt") or "requirements" in body_lower:
                return "deps", "python", 0.9, f"Detected Python dependencies (pattern: {pattern[:30]})"
    
    for pattern in PATTERNS["deps_node"]:
        if re.search(pattern, body, re.MULTILINE):
            if lang in ("json", "") and '"dependencies"' in body:
                return "deps", "node", 0.8, "Detected Node.js package.json"
    
    # Check for run commands
    for pattern in PATTERNS["run"]:
        if re.search(pattern, first_lines, re.MULTILINE):
            if lang in ("bash", "sh", "shell", "console", ""):
                return "run", lang or "bash", 0.85, f"Detected run command (pattern: {pattern[:30]})"
    
    # Check for file patterns
    for file_type, patterns in PATTERNS.items():
        if not file_type.startswith("file_"):
            continue
        for pattern in patterns:
            if re.search(pattern, first_lines, re.MULTILINE):
                detected_lang = file_type.replace("file_", "")
                return "file", detected_lang, 0.8, f"Detected {detected_lang} file content"
    
    # Fallback: if language is specified, assume it's a file
    if lang and lang not in ("bash", "sh", "shell", "console", "text", "txt", ""):
        return "file", lang, 0.6, f"Assuming file based on language tag: {lang}"
    
    return "", "", 0.0, "Could not determine block type"


def suggest_filename(lang: str, body: str, index: int) -> str:
    """Suggest a filename for a file block."""
    ext = LANG_EXTENSIONS.get(lang, f".{lang}" if lang else ".txt")
    
    # Try to detect class/function name for Python
    if lang in ("python", "py"):
        # Check for Flask/FastAPI app
        if re.search(r"app\s*=\s*(Flask|FastAPI)\(", body):
            return f"app{ext}"
        # Check for class definition
        match = re.search(r"^class\s+(\w+)", body, re.MULTILINE)
        if match:
            return f"{match.group(1).lower()}{ext}"
        # Check for main block
        if '__name__' in body and '__main__' in body:
            return f"main{ext}"
    
    # Check for HTML structure
    if lang in ("html",):
        if "<title>" in body:
            match = re.search(r"<title>([^<]+)</title>", body)
            if match:
                name = match.group(1).lower().replace(" ", "_")[:20]
                return f"{name}.html"
        return "index.html"
    
    # Default naming
    return f"file_{index}{ext}"


def convert_markdown_to_markpact(text: str, verbose: bool = True) -> ConversionResult:
    """
    Convert regular Markdown to markpact format.
    
    Analyzes code blocks and converts them to markpact:* format based on heuristics.
    """
    result = ConversionResult(original_text=text, converted_text=text)
    
    # Check if already has markpact blocks
    if re.search(r"^```(?:[^\s]+\s+)?markpact:", text, re.MULTILINE):
        result.has_markpact = True
        result.changes.append("File already contains markpact blocks")
        return result
    
    # Find all fenced code blocks
    pattern = re.compile(
        r"^```(\w*)\n(.*?)\n^```",
        re.MULTILINE | re.DOTALL
    )
    
    file_index = 0
    deps_found = False
    run_found = False
    
    def replace_block(match: re.Match) -> str:
        nonlocal file_index, deps_found, run_found
        
        lang = match.group(1) or ""
        body = match.group(2)
        
        # Detect block type
        tag, meta, confidence, reason = detect_block_type(lang, body)
        
        if not tag or confidence < 0.5:
            # Keep original if uncertain
            return match.group(0)
        
        # Build markpact tag
        if tag == "deps":
            if meta == "python" and deps_found:
                # Already have deps, skip
                return match.group(0)
            deps_found = True
            new_tag = f"```text markpact:deps {meta}"
            result.changes.append(f"[CONVERT] ```{lang} → ```text markpact:deps {meta} ({reason})")
        
        elif tag == "run":
            if run_found:
                # Already have run, skip
                return match.group(0)
            run_found = True
            new_tag = f"```{meta or 'bash'} markpact:run"
            result.changes.append(f"[CONVERT] ```{lang} → ```{meta or 'bash'} markpact:run ({reason})")
        
        elif tag == "file":
            filename = suggest_filename(meta, body, file_index)
            file_index += 1
            new_tag = f"```{meta} markpact:file path={filename}"
            result.changes.append(f"[CONVERT] ```{lang} → ```{meta} markpact:file path={filename} ({reason})")
        
        else:
            return match.group(0)
        
        # Create converted block record
        result.blocks.append(ConvertedBlock(
            original_lang=lang,
            markpact_tag=tag,
            meta=meta,
            body=body,
            confidence=confidence,
            reason=reason,
        ))
        
        return f"{new_tag}\n{body}\n```"
    
    result.converted_text = pattern.sub(replace_block, text)
    
    if not result.changes:
        result.changes.append("No convertible code blocks found")
    
    return result


def print_conversion_report(result: ConversionResult) -> None:
    """Print a report of the conversion."""
    print("\n" + "=" * 60)
    print("MARKPACT CONVERSION REPORT")
    print("=" * 60)
    
    if result.has_markpact:
        print("\n✓ File already contains markpact blocks. No conversion needed.")
        return
    
    if not result.blocks:
        print("\n⚠ No convertible code blocks found.")
        print("  Add code blocks with language tags for better detection.")
        return
    
    print(f"\n✓ Converted {len(result.blocks)} block(s):\n")
    
    for change in result.changes:
        print(f"  {change}")
    
    print("\n" + "-" * 60)
    print("Summary:")
    
    deps = [b for b in result.blocks if b.markpact_tag == "deps"]
    files = [b for b in result.blocks if b.markpact_tag == "file"]
    runs = [b for b in result.blocks if b.markpact_tag == "run"]
    
    if deps:
        print(f"  • Dependencies: {len(deps)} block(s)")
    if files:
        print(f"  • Files: {len(files)} file(s)")
        for f in files:
            print(f"      - {f.meta}")
    if runs:
        print(f"  • Run command: {len(runs)} block(s)")
    
    print("=" * 60 + "\n")
