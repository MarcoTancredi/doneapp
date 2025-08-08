from fastapi import FastAPI, Request, Form

from fastapi.responses import HTMLResponse, RedirectResponse

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import subprocess

import sys

import os



app = FastAPI(title="Done — Patch UI")



BASE_DIR = Path(__file__).resolve().parent.parent

INBOX = BASE_DIR / "inbox" / "patch_input.txt"

TEMPLATES_DIR = BASE_DIR / "app" / "templates"

TOOLS_DIR = BASE_DIR / "tools"



env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))



def run_apply_changes() -> str:

    """

    Executa o aplicador diretamente (sem depender do .bat) e captura a saída.

    """

    cmd = [sys.executable, str(TOOLS_DIR / "apply_changes.py"), "--input", str(INBOX)]

    try:

        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR), timeout=120)

        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")

        return out.strip() or "[sem saída]"

    except Exception as e:

        return f"[erro ao executar aplicador] {e}"



@app.get("/", response_class=HTMLResponse)

async def login_view(request: Request):

    tpl = env.get_template("login.html")

    return tpl.render()



@app.post("/login", response_class=HTMLResponse)

async def login_post(email: str = Form(...), password: str = Form(...)):

    # Placeholder — autenticação real virá depois

    ok_html = "<html><body style='background:#0e0e10;color:#e4e4e7;font-family:system-ui'><h2>Login recebido</h2><p>Em breve validaremos os dados.</p><a href='/' style='color:#7df9ff'>Voltar</a></body></html>"

    return HTMLResponse(ok_html)



@app.get("/cadastro", response_class=HTMLResponse)

async def cadastro_view(request: Request):

    tpl = env.get_template("cadastro.html")

    return tpl.render()



@app.post("/cadastro", response_class=HTMLResponse)

async def cadastro_submit(

    user: str = Form(...),

    email: str = Form(...),

    password: str = Form(...),

    password2: str = Form(...),

    phone: str = Form(""),

    company: str = Form(""),

    auth_email: str = Form("0"),

    auth_sms: str = Form("0"),

    auth_whatsapp: str = Form("0"),

    auth_phone: str = Form("0"),

    auth_admin: str = Form("0"),

):

    # Placeholder — persistência virá depois

    ok_html = "<html><body style='background:#0e0e10;color:#e4e4e7;font-family:system-ui'><h2>Cadastro recebido ✅</h2><p>Em breve validaremos os dados.</p><a href='/cadastro' style='color:#7df9ff'>Voltar</a></body></html>"

    return HTMLResponse(ok_html)



@app.get("/updota", response_class=HTMLResponse)

async def updota_view(request: Request):

    tpl = env.get_template("index.html")

    clear = request.query_params.get("clear")

    current = "" if clear else ""

    return tpl.render(current=current)



@app.post("/updota/apply", response_class=HTMLResponse)

async def updota_apply(patch: str = Form(...)):

    INBOX.parent.mkdir(parents=True, exist_ok=True)

    INBOX.write_text(patch, encoding="utf-8")

    output = run_apply_changes()

    # Mostra a saída no mesmo textarea (substitui o conteúdo)

    tpl = env.get_template("index.html")

    return tpl.render(current=output)