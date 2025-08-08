from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import sys
import os
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
TEMPLATES_DIR = APP_DIR / "templates"
INBOX_DIR = BASE_DIR / "inbox"
TOOLS_DIR = BASE_DIR / "tools"

INBOX_DIR.mkdir(exist_ok=True, parents=True)

app = FastAPI(title="Done — Patch UI")

# (Opcional) servir /static se criarmos assets futuramente
STATIC_DIR = APP_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request, msg: str | None = None, ok: int = 0):
    """
    Tela de login. Mensagens curtas são colocadas em 'msg'.
    ok=1 -> mensagem verde; ok=0 -> mensagem vermelha.
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "msg": msg, "ok": ok}
    )


@app.get("/cadastro", response_class=HTMLResponse)
async def get_cadastro(request: Request, msg: str | None = None, ok: int = 0):
    return templates.TemplateResponse(
        "cadastro.html",
        {"request": request, "msg": msg, "ok": ok}
    )


@app.post("/cadastro", response_class=HTMLResponse)
async def post_cadastro(
    request: Request,
    fullname: str = Form(""),
    username: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    agree: str = Form("")
):
    # Aqui, por enquanto, apenas simulamos o recebimento
    # e voltamos ao login com a mensagem por 3 segundos (JS no template).
    return RedirectResponse(url="/login?msg=Cadastro%20recebido%2C%20aguarde%20libera%C3%A7%C3%A3o&ok=1", status_code=302)


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    # Placeholder simples: depois trocamos pela dashboard real
    html = """
    <html><head><meta charset="utf-8"><title>Home</title>
    <style>
      body{background:#0a0f1f;color:#e5f1ff;font-family:Inter,system-ui,Arial}
      .wrap{height:100vh;display:flex;align-items:center;justify-content:center}
      .card{width:min(900px,92vw);background:rgba(10,20,40,.8);padding:24px;border-radius:16px;
            box-shadow:0 20px 60px rgba(0,255,200,.15), inset 0 0 0 1px rgba(0,255,200,.15)}
    </style></head>
    <body><div class="wrap"><div class="card">
      <h2>Bem-vindo 👋</h2>
      <p>A UI principal virá aqui. Clique na engrenagem (futuro) para Config.</p>
      <p><a href="/updota" style="color:#6cf">/updota</a> para aplicar patches.</p>
    </div></div></body></html>
    """
    return HTMLResponse(html)


# ====== UPDOTA (UI de patch) ======

@app.get("/updota", response_class=HTMLResponse)
async def updota_get(request: Request, last_output: str | None = None):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "last_output": last_output or ""}
    )


@app.post("/updota", response_class=HTMLResponse)
async def updota_post(request: Request, patch: str = Form("")):
    # Salva o patch e executa o aplicador
    INBOX_DIR.mkdir(exist_ok=True, parents=True)
    patch_file = INBOX_DIR / "patch_input.txt"
    patch_file.write_text(patch, encoding="utf-8")

    cmd = [sys.executable, str(TOOLS_DIR / "apply_changes.py"), "--input", str(patch_file)]
    try:
        completed = subprocess.run(
            cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8"
        )
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    except Exception as e:
        output = f"[ERRO] Falha ao executar o aplicador: {e!r}"

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "last_output": output}
    )


@app.post("/_dev/reload", response_class=PlainTextResponse)
async def dev_reload():
    """
    Toca um arquivo .reload para o reloader detectar mudança e recarregar.
    Útil após aplicar patches que alterem rotas/templates.
    """
    Path(".reload").write_text(datetime.datetime.now().isoformat(), encoding="utf-8")
    return PlainTextResponse("reload touch OK")