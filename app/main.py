from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import subprocess
import sys
import json

app = FastAPI(title="Done — Patch UI")

BASE_DIR = Path(__file__).resolve().parent.parent
INBOX = BASE_DIR / "inbox" / "patch_input.txt"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
TOOLS_DIR = BASE_DIR / "tools"
CFG_PATH = BASE_DIR / "app" / "config" / "ui.json"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
def load_ui_cfg() -> dict:
    """Lê arquivo de configuração de UI; se não existir, retorna defaults seguros."""
    try:
        if CFG_PATH.exists():
            return json.loads(CFG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "success_color": "#22c55e",
        "success_ms": 1000,
        "error_color": "#ef4444",
        "error_ms": 3000,
        "social_enabled": {
            "youtube": False, "tiktok": False, "github": False, "facebook": False
        }
    }

def run_apply_changes() -> str:
    """Executa o aplicador e captura a saída (sem depender do .bat)."""
    cmd = [sys.executable, str(TOOLS_DIR / "apply_changes.py"), "--input", str(INBOX)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(BASE_DIR), timeout=180
        )
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return out.strip() or "[sem saída]"
    except Exception as e:
        return f"[erro ao executar aplicador] {e}"

# -----------------------
# Rotas de UI
# -----------------------

@app.get("/", response_class=HTMLResponse)
async def login_view(request: Request):
    tpl = env.get_template("login.html")
    cfg = load_ui_cfg()
    return tpl.render(cfg=cfg)

@app.post("/login", response_class=HTMLResponse)
async def login_post(
    email: str = Form(...),
    password: str = Form(...),
    keep: str = Form("0"),
):
    # Placeholder — a UI do login (JS) já trata feedback e redireciona para /home
    cfg = load_ui_cfg()
    color = cfg.get("success_color", "#22c55e")
    ms = int(cfg.get("success_ms", 1000))
    ok_html = (
        "<html><body style='background:#0e0e10;color:#e4e4e7;font-family:system-ui'>"
        f"<h2 style='color:{color};'>Login recebido</h2>"
        "<p>Autenticação real será ligada ao backend em breve.</p>"
        "<a href='/' style='color:#7df9ff'>Voltar</a>"
        f"<script>setTimeout(function(){{}}, {ms});</script>"
        "</body></html>"
    )
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
    # Placeholder — persistência virá na etapa de backend
    cfg = load_ui_cfg()
    color = cfg.get("success_color", "#22c55e")
    ms = int(cfg.get("success_ms", 1000))
    ok_html = (
        "<html><body style='background:#0e0e10;color:#e4e4e7;font-family:system-ui'>"
        f"<h2 style='color:{color};'>Cadastro recebido ✅</h2>"
        "<p>Em breve validaremos os dados.</p>"
        "<a href='/cadastro' style='color:#7df9ff'>Voltar</a>"
        f"<script>setTimeout(function(){{}}, {ms});</script>"
        "</body></html>"
    )
    return HTMLResponse(ok_html)

# -----------------------
# Módulo de Patch (/updota)
# -----------------------

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
    tpl = env.get_template("index.html")
    return tpl.render(current=output)

# -----------------------
# Pós-login e Config
# -----------------------

@app.get("/home", response_class=HTMLResponse)
async def home_view(request: Request):
    tpl = env.get_template("home.html")
    return tpl.render()

@app.get("/config", response_class=HTMLResponse)
async def config_view(request: Request):
    tpl = env.get_template("config.html")
    return tpl.render()