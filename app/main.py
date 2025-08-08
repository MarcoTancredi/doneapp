from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

app = FastAPI(title="Done — Patch UI")

BASE_DIR = Path(__file__).resolve().parent.parent
INBOX = BASE_DIR / "inbox" / "patch_input.txt"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    tpl = env.get_template("index.html")
    current = ""
    if INBOX.exists():
        current = INBOX.read_text(encoding="utf-8")
    return tpl.render(current=current)

@app.post("/apply", response_class=HTMLResponse)
async def apply(patch: str = Form(...)):
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    INBOX.write_text(patch, encoding="utf-8")
    return RedirectResponse(url="/?saved=1", status_code=303)

@app.get("/cadastro", response_class=HTMLResponse)
async def cadastro(request: Request):
    tpl = env.get_template("cadastro.html")
    return tpl.render()

@app.post("/cadastro", response_class=HTMLResponse)
async def cadastro_submit(
    user: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    company: str = Form(""),
    auth_email: str = Form("0"),
    auth_sms: str = Form("0"),
    auth_whatsapp: str = Form("0"),
    auth_phone: str = Form("0"),
    auth_admin: str = Form("0"),
):
    # Por enquanto apenas retorna um HTML simples de confirmação
    ok_html = """
    <html><body style='background:#0e0e10;color:#e4e4e7;font-family:system-ui'>
    <h2>Cadastro recebido ✅</h2>
    <p>Em breve validaremos os dados.</p>
    <a href='/cadastro' style='color:#7df9ff'>Voltar</a>
    </body></html>
    """
    return HTMLResponse(ok_html)