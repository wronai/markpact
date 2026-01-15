"""Convert notebook formats to markpact README.md

Supported formats:
- .ipynb (Jupyter Notebook)
- .Rmd (R Markdown)
- .qmd (Quarto Markdown)
- .dib (Databricks Notebook)
- .zpln (Zeppelin Notebook)
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class NotebookCell:
    """Represents a cell in a notebook."""
    cell_type: str  # 'code', 'markdown', 'raw'
    source: str
    language: str = "python"
    outputs: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class Notebook:
    """Represents a parsed notebook."""
    cells: list[NotebookCell]
    metadata: dict = field(default_factory=dict)
    language: str = "python"
    title: str = ""
    description: str = ""


def detect_format(path: Path) -> Optional[str]:
    """Detect notebook format from file extension."""
    ext = path.suffix.lower()
    format_map = {
        '.ipynb': 'jupyter',
        '.rmd': 'rmarkdown',
        '.qmd': 'quarto',
        '.dib': 'databricks',
        '.zpln': 'zeppelin',
        '.jl': 'pluto',
    }
    return format_map.get(ext)


def parse_jupyter(path: Path) -> Notebook:
    """Parse Jupyter .ipynb notebook."""
    content = json.loads(path.read_text(encoding='utf-8'))
    
    # Extract metadata
    metadata = content.get('metadata', {})
    kernel_info = metadata.get('kernelspec', {})
    language = kernel_info.get('language', 'python')
    
    cells = []
    for cell in content.get('cells', []):
        cell_type = cell.get('cell_type', 'code')
        source = cell.get('source', [])
        if isinstance(source, list):
            source = ''.join(source)
        
        outputs = cell.get('outputs', [])
        cell_metadata = cell.get('metadata', {})
        
        cells.append(NotebookCell(
            cell_type=cell_type,
            source=source,
            language=language,
            outputs=outputs,
            metadata=cell_metadata,
        ))
    
    # Try to extract title from first markdown cell
    title = path.stem
    description = ""
    for cell in cells:
        if cell.cell_type == 'markdown':
            lines = cell.source.strip().split('\n')
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            # Get description from first paragraph
            desc_lines = []
            for line in lines:
                if not line.startswith('#') and line.strip():
                    desc_lines.append(line.strip())
                elif desc_lines:
                    break
            description = ' '.join(desc_lines)[:200]
            break
    
    return Notebook(
        cells=cells,
        metadata=metadata,
        language=language,
        title=title,
        description=description,
    )


def parse_rmarkdown(path: Path) -> Notebook:
    """Parse R Markdown .Rmd file."""
    content = path.read_text(encoding='utf-8')
    
    cells = []
    metadata = {}
    title = path.stem
    description = ""
    
    # Parse YAML front matter
    yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)
        # Simple YAML parsing for title
        for line in yaml_content.split('\n'):
            if line.startswith('title:'):
                title = line.split(':', 1)[1].strip().strip('"\'')
            elif line.startswith('output:'):
                metadata['output'] = line.split(':', 1)[1].strip()
        content = content[yaml_match.end():]
    
    # Parse code chunks and markdown
    # R Markdown code chunks: ```{r chunk_name, options}
    pattern = r'```\{(\w+)(?:\s+([^}]*))?\}(.*?)```'
    
    last_end = 0
    for match in re.finditer(pattern, content, re.DOTALL):
        # Add markdown before this chunk
        md_content = content[last_end:match.start()].strip()
        if md_content:
            cells.append(NotebookCell(
                cell_type='markdown',
                source=md_content,
                language='markdown',
            ))
        
        # Add code chunk
        lang = match.group(1)
        chunk_opts = match.group(2) or ""
        code = match.group(3).strip()
        
        cells.append(NotebookCell(
            cell_type='code',
            source=code,
            language=lang,
            metadata={'chunk_options': chunk_opts},
        ))
        
        last_end = match.end()
    
    # Add remaining markdown
    remaining = content[last_end:].strip()
    if remaining:
        cells.append(NotebookCell(
            cell_type='markdown',
            source=remaining,
            language='markdown',
        ))
    
    # Get description from first markdown cell
    for cell in cells:
        if cell.cell_type == 'markdown' and cell.source.strip():
            lines = [l for l in cell.source.split('\n') if l.strip() and not l.startswith('#')]
            description = ' '.join(lines)[:200]
            break
    
    return Notebook(
        cells=cells,
        metadata=metadata,
        language='r',
        title=title,
        description=description,
    )


def parse_quarto(path: Path) -> Notebook:
    """Parse Quarto .qmd file (similar to R Markdown but multi-language)."""
    content = path.read_text(encoding='utf-8')
    
    cells = []
    metadata = {}
    title = path.stem
    description = ""
    default_language = "python"
    
    # Parse YAML front matter
    yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)
        for line in yaml_content.split('\n'):
            if line.startswith('title:'):
                title = line.split(':', 1)[1].strip().strip('"\'')
            elif line.startswith('jupyter:'):
                default_language = 'python'
            elif line.startswith('engine:'):
                engine = line.split(':', 1)[1].strip()
                if 'knitr' in engine:
                    default_language = 'r'
        content = content[yaml_match.end():]
    
    # Parse code chunks (Quarto uses ```{python} or ```{r} syntax)
    pattern = r'```\{(\w+)(?:\s+([^}]*))?\}(.*?)```'
    
    last_end = 0
    for match in re.finditer(pattern, content, re.DOTALL):
        md_content = content[last_end:match.start()].strip()
        if md_content:
            cells.append(NotebookCell(
                cell_type='markdown',
                source=md_content,
                language='markdown',
            ))
        
        lang = match.group(1)
        chunk_opts = match.group(2) or ""
        code = match.group(3).strip()
        
        cells.append(NotebookCell(
            cell_type='code',
            source=code,
            language=lang,
            metadata={'chunk_options': chunk_opts},
        ))
        
        last_end = match.end()
    
    remaining = content[last_end:].strip()
    if remaining:
        cells.append(NotebookCell(
            cell_type='markdown',
            source=remaining,
            language='markdown',
        ))
    
    return Notebook(
        cells=cells,
        metadata=metadata,
        language=default_language,
        title=title,
        description=description,
    )


def parse_zeppelin(path: Path) -> Notebook:
    """Parse Zeppelin .zpln notebook."""
    content = json.loads(path.read_text(encoding='utf-8'))
    
    cells = []
    title = content.get('name', path.stem)
    
    for paragraph in content.get('paragraphs', []):
        text = paragraph.get('text', '')
        
        # Zeppelin uses %interpreter prefix
        if text.startswith('%md'):
            cells.append(NotebookCell(
                cell_type='markdown',
                source=text[3:].strip(),
                language='markdown',
            ))
        elif text.startswith('%python'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[7:].strip(),
                language='python',
            ))
        elif text.startswith('%spark'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[6:].strip(),
                language='scala',
            ))
        elif text.startswith('%sql'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[4:].strip(),
                language='sql',
            ))
        elif text.startswith('%r'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[2:].strip(),
                language='r',
            ))
        else:
            # Default to code
            cells.append(NotebookCell(
                cell_type='code',
                source=text.strip(),
                language='python',
            ))
    
    return Notebook(
        cells=cells,
        metadata=content.get('config', {}),
        language='python',
        title=title,
        description="",
    )


def parse_databricks(path: Path) -> Notebook:
    """Parse Databricks .dib notebook."""
    content = json.loads(path.read_text(encoding='utf-8'))
    
    cells = []
    title = path.stem
    default_language = content.get('language', 'python')
    
    for command in content.get('commands', []):
        text = command.get('command', '')
        
        # Databricks uses %language prefix similar to Zeppelin
        if text.startswith('%md'):
            cells.append(NotebookCell(
                cell_type='markdown',
                source=text[3:].strip(),
                language='markdown',
            ))
        elif text.startswith('%python'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[7:].strip(),
                language='python',
            ))
        elif text.startswith('%scala'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[6:].strip(),
                language='scala',
            ))
        elif text.startswith('%sql'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[4:].strip(),
                language='sql',
            ))
        elif text.startswith('%r'):
            cells.append(NotebookCell(
                cell_type='code',
                source=text[2:].strip(),
                language='r',
            ))
        else:
            cells.append(NotebookCell(
                cell_type='code',
                source=text.strip(),
                language=default_language,
            ))
    
    return Notebook(
        cells=cells,
        metadata=content.get('metadata', {}),
        language=default_language,
        title=title,
        description="",
    )


def parse_notebook(path: Path) -> Notebook:
    """Parse notebook file based on format."""
    fmt = detect_format(path)
    
    if fmt == 'jupyter':
        return parse_jupyter(path)
    elif fmt == 'rmarkdown':
        return parse_rmarkdown(path)
    elif fmt == 'quarto':
        return parse_quarto(path)
    elif fmt == 'zeppelin':
        return parse_zeppelin(path)
    elif fmt == 'databricks':
        return parse_databricks(path)
    else:
        raise ValueError(f"Unsupported notebook format: {path.suffix}")


def extract_dependencies(notebook: Notebook) -> list[str]:
    """Extract dependencies from notebook code cells."""
    deps = set()
    
    # Common Python import patterns
    import_patterns = [
        r'^import\s+(\w+)',
        r'^from\s+(\w+)',
    ]
    
    # Standard library modules to exclude
    stdlib = {
        'os', 'sys', 're', 'json', 'csv', 'math', 'random', 'datetime',
        'collections', 'itertools', 'functools', 'pathlib', 'typing',
        'subprocess', 'shutil', 'tempfile', 'io', 'time', 'logging',
        'unittest', 'argparse', 'copy', 'pickle', 'hashlib', 'base64',
        'threading', 'multiprocessing', 'socket', 'http', 'urllib',
        'sqlite3', 'dataclasses', 'enum', 'abc', 'contextlib',
    }
    
    for cell in notebook.cells:
        if cell.cell_type == 'code' and cell.language == 'python':
            for line in cell.source.split('\n'):
                line = line.strip()
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        module = match.group(1)
                        if module not in stdlib:
                            deps.add(module)
    
    # Add runtime dependencies based on framework
    if 'fastapi' in deps:
        deps.add('uvicorn')
    if 'flask' in deps:
        deps.add('gunicorn')
    if 'streamlit' in deps:
        deps.add('watchdog')
    
    return sorted(deps)


def suggest_run_command(notebook: Notebook) -> str:
    """Suggest a run command based on notebook content."""
    has_flask = False
    has_fastapi = False
    has_streamlit = False
    has_dash = False
    
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            code = cell.source.lower()
            if 'flask' in code:
                has_flask = True
            if 'fastapi' in code:
                has_fastapi = True
            if 'streamlit' in code:
                has_streamlit = True
            if 'dash' in code:
                has_dash = True
    
    if has_streamlit:
        return "streamlit run app.py --server.port ${MARKPACT_PORT:-8501}"
    elif has_fastapi:
        return "uvicorn app:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}"
    elif has_flask:
        return "flask run --host 0.0.0.0 --port ${MARKPACT_PORT:-5000}"
    elif has_dash:
        return "python app.py"
    else:
        return "python main.py"


def notebook_to_markpact(
    notebook: Notebook,
    output_path: Optional[Path] = None,
    verbose: bool = True,
) -> str:
    """Convert notebook to markpact README.md format."""
    
    lines = []
    
    # Title and description
    lines.append(f"# {notebook.title}")
    lines.append("")
    if notebook.description:
        lines.append(notebook.description)
        lines.append("")
    
    # Add run instructions
    lines.append("## Uruchomienie")
    lines.append("")
    lines.append("```bash")
    if output_path:
        lines.append(f"markpact {output_path}")
    else:
        lines.append("markpact README.md")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Extract and add dependencies
    deps = extract_dependencies(notebook)
    if deps:
        lines.append(f"```markpact:deps {notebook.language}")
        for dep in deps:
            lines.append(dep)
        lines.append("```")
        lines.append("")
    
    # Process cells - collect code and markdown separately
    code_cells = []
    markdown_sections = []
    current_file_content = []
    current_file_name = "app.py"
    file_counter = 0
    skip_first_title = True  # Skip first markdown with title
    
    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            source = cell.source.strip()
            
            # Skip first cell if it's the title we already used
            if skip_first_title:
                skip_first_title = False
                # Check if this is just title/description we already captured
                lines_in_cell = source.split('\n')
                has_only_title = all(
                    l.startswith('#') or not l.strip() or l.strip() == notebook.description.strip()
                    for l in lines_in_cell
                )
                if has_only_title:
                    continue
            
            # If we have accumulated code, save it first
            if current_file_content:
                code_cells.append((current_file_name, '\n'.join(current_file_content)))
                current_file_content = []
                file_counter += 1
            
            # Add markdown section header only (not full content to avoid duplication)
            for line in source.split('\n'):
                if line.startswith('##'):
                    markdown_sections.append(line)
                    break
            
        elif cell.cell_type == 'code':
            source = cell.source.strip()
            
            if not source:
                continue
            
            # Check for file path hints in comments
            file_match = re.match(r'^#\s*(?:file:|path:)\s*(\S+)', source)
            if file_match:
                if current_file_content:
                    code_cells.append((current_file_name, '\n'.join(current_file_content)))
                    current_file_content = []
                current_file_name = file_match.group(1)
                source = '\n'.join(source.split('\n')[1:])
            
            # For notebooks, keep all code in single app.py for simplicity
            # This avoids import issues between generated files
            current_file_name = 'app.py'
            current_file_content.append(source)
    
    # Save remaining code
    if current_file_content:
        code_cells.append((current_file_name, '\n'.join(current_file_content)))
    
    # Merge code into appropriate files
    merged_files = {}
    for filename, content in code_cells:
        if filename in merged_files:
            merged_files[filename] += '\n\n' + content
        else:
            merged_files[filename] = content
    
    # Add file blocks
    for filename, content in merged_files.items():
        lang = notebook.language
        if filename.endswith('.py'):
            lang = 'python'
        elif filename.endswith('.r') or filename.endswith('.R'):
            lang = 'r'
        elif filename.endswith('.js'):
            lang = 'javascript'
        
        lines.append(f"```markpact:file {lang} path={filename}")
        lines.append(content)
        lines.append("```")
        lines.append("")
    
    # Add run command
    run_cmd = suggest_run_command(notebook)
    lines.append(f"```markpact:run {notebook.language}")
    lines.append(run_cmd)
    lines.append("```")
    lines.append("")
    
    result = '\n'.join(lines)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding='utf-8')
        if verbose:
            print(f"[markpact] Converted {notebook.title} to {output_path}")
    
    return result


def convert_notebook(
    input_path: Path,
    output_path: Optional[Path] = None,
    verbose: bool = True,
) -> str:
    """Convert a notebook file to markpact format.
    
    Args:
        input_path: Path to notebook file (.ipynb, .Rmd, .qmd, etc.)
        output_path: Optional output path for README.md
        verbose: Print progress messages
        
    Returns:
        Converted markpact README content
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Notebook not found: {input_path}")
    
    fmt = detect_format(input_path)
    if not fmt:
        raise ValueError(f"Unsupported notebook format: {input_path.suffix}")
    
    if verbose:
        print(f"[markpact] Converting {fmt} notebook: {input_path}")
    
    notebook = parse_notebook(input_path)
    
    if verbose:
        print(f"[markpact] Found {len(notebook.cells)} cells, language: {notebook.language}")
    
    return notebook_to_markpact(notebook, output_path, verbose)


def get_supported_formats() -> dict[str, str]:
    """Get dictionary of supported notebook formats."""
    return {
        '.ipynb': 'Jupyter Notebook',
        '.rmd': 'R Markdown',
        '.qmd': 'Quarto Markdown',
        '.dib': 'Databricks Notebook',
        '.zpln': 'Zeppelin Notebook',
    }
