# markpact


## Run shell
![img_1.png](img_1.png)


def parse_blocks(text):
    return CODEBLOCK_RE.finditer(text)

def write_file(path, content):
    full = SANDBOX / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    print(f"[markpact] wrote {full}")

 def run(cmd):
     print(f"[markpact] RUN: {cmd}")
     env = os.environ.copy()
     venv_bin = SANDBOX / ".venv" / "bin"
     if venv_bin.exists():
         env["VIRTUAL_ENV"] = str(SANDBOX / ".venv")
         env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
     subprocess.check_call(cmd, shell=True, cwd=SANDBOX, env=env)

 def ensure_venv():
     venv_dir = SANDBOX / ".venv"
     python = venv_dir / "bin" / "python"
     if python.exists():
         return
     run(f"{sys.executable} -m venv .venv")

def main():
    text = README.read_text()
    blocks = list(parse_blocks(text))

    deps = {"python": [], "node": [], "system": []}
    run_cmd = None

    for block in blocks:
        kind = block.group("kind")
        meta = (block.group("meta") or "").strip()
        body = block.group("body").strip()

        if kind == "file":
            path = meta.split("=")[1]  # np. path=app/main.py
            write_file(path, body)

        elif kind == "deps":
            deps[meta].extend(line.strip() for line in body.splitlines() if line.strip())

        elif kind == "run":
            run_cmd = body

    # Python deps
    if deps["python"]:
        ensure_venv()
        req_file = SANDBOX / "requirements.txt"
        req_file.write_text("\n".join(deps["python"]))
        run(".venv/bin/pip install -r requirements.txt")

    # Run command
    if run_cmd:
        run(run_cmd)
    else:
        print("[markpact] No run command defined")

if __name__ == "__main__":
    main()
```

## 2️⃣ Dependencies

```markpact:deps python
fastapi
uvicorn
```

---

## 3️⃣ Application Files

```markpact:file python path=app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from Executable Markdown"}
```

---

## 4️⃣ Run Command

```markpact:run python
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
