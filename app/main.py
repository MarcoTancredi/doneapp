# Ação: CRIAR/SUBSTITUIR
# Local: app/main.py
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
import subprocess
import sys
import os
import datetime

# Diretórios base
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
TEMPLATES_DIR = APP_DIR / "templates"
TOOLS_DIR = ROOT_DIR / "tools"
INBOX_DIR = ROOT_DIR / "inbox"
BACKUPS_DIR = ROOT_DIR / "backups"

# Garante pastas necessárias
INBOX_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

# Jinja
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI(title="Done — Patch UI")

# ---------- Rotas básicas ----------
@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    # Redireciona para /login por enquanto
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login() -> HTMLResponse:
    tpl = env.get_template("login.html")
    return HTMLResponse(tpl.render())

@app.get("/cadastro", response_class=HTMLResponse)
def cadastro() -> HTMLResponse:
    tpl = env.get_template("cadastro.html")
    return HTMLResponse(tpl.render())

# ---------- UPDOTA (aplicador de patches) ----------
@app.get("/updota", response_class=HTMLResponse)
def updota_get() -> HTMLResponse:
    tpl = env.get_template("updota.html")
    return HTMLResponse(
        tpl.render(
            repo=str(ROOT_DIR),
            tools=str(TOOLS_DIR),
            inbox=str(INBOX_DIR),
            backups=str(BACKUPS_DIR),
        )
    )

@app.post("/updota/apply", response_class=HTMLResponse)
def updota_apply(patch: str = Form(...)) -> HTMLResponse:
    # Salva o patch
    patch_file = INBOX_DIR / "patch_input.txt"
    patch_file.write_text(patch, encoding="utf-8")

    # Executa o aplicador
    apply_script = TOOLS_DIR / "apply_changes.py"
    cmd = [
        sys.executable,
        str(apply_script),
        "--input",
        str(patch_file),
        "--repo",
        str(ROOT_DIR),
        "--backups",
        str(BACKUPS_DIR),
    ]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=120
        )
        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    except Exception as e:
        output = f"[ERRO] Falha ao executar apply_changes.py: {e}"

    # Renderiza com a saída na mesma tela
    tpl = env.get_template("updota.html")
    return HTMLResponse(
        tpl.render(
            repo=str(ROOT_DIR),
            tools=str(TOOLS_DIR),
            inbox=str(INBOX_DIR),
            backups=str(BACKUPS_DIR),
            result=output,
            flash_ok="Patch aplicado (verifique a saída).",
        )
    )

@app.post("/updota/restart", response_class=JSONResponse)
def updota_restart():
    """
    Força reload do servidor em modo --reload tocando um arquivo .reload.
    O WatchFiles detecta a alteração e reinicia.
    """
    try:
        reload_flag = ROOT_DIR / ".reload"
        reload_flag.write_text(datetime.datetime.now().isoformat(), encoding="utf-8")
        return JSONResponse({"ok": True, "message": "Solicitada reinicialização."})
    except Exception as e:
        return JSONResponse({"ok": False, "message": f"Erro: {e}"}, status_code=500)