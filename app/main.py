from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

app = FastAPI(title=“Done — Patch UI”)

BASE_DIR = Path(file).resolve().parent.parent
INBOX = BASE_DIR / “inbox” / “patch_input.txt”
TEMPLATES_DIR = BASE_DIR / “app” / “templates”

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

@app.get(”/”, response_class=HTMLResponse)
async def index(request: Request):
tpl = env.get_template(“index.html”)
current = “”
if INBOX.exists():
current = INBOX.read_text(encoding=“utf-8”)
return tpl.render(current=current)

@app.post(”/apply”, response_class=HTMLResponse)
async def apply(patch: str = Form(…)):
INBOX.parent.mkdir(parents=True, exist_ok=True)
INBOX.write_text(patch, encoding=“utf-8”)
return RedirectResponse(url=”/?saved=1”, status_code=303)