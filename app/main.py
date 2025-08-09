from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import subprocess
import sys
from pathlib import Path
import asyncio
import threading

# TOO/APP/MAIAA - App FastAPI principal
app = FastAPI(title="DoneApp", description="Publicacao Multicanal Automatizada")

templates = Jinja2Templates(directory="app/templates")

# Criar diretorio static se nao existir
static_dir = Path("app/static")
static_dir.mkdir(parents=True, exist_ok=True)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Redireciona para /login"""
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Tela de login com UI Neon responsiva"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/cadastro", response_class=HTMLResponse)
async def cadastro_page(request: Request):
    """Tela de cadastro com checklist de autenticacao"""
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.get("/updota", response_class=HTMLResponse)
async def updota_page(request: Request):
    """UI para aplicar patches (admin only)"""
    return templates.TemplateResponse("updota.html", {"request": request})

@app.post("/updota/apply")
async def apply_patch(request: Request, patch_content: str = Form(...)):
    """Aplica patch enviado via formulario"""
    try:
        # Criar diretorio inbox se nao existir
        inbox_dir = Path("inbox")
        inbox_dir.mkdir(exist_ok=True)
        
        # Salvar patch no arquivo
        patch_file = inbox_dir / "patch_input.txt"
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(patch_content)
        
        # Executar apply_changes.py
        result = subprocess.run([
            sys.executable, "tools/apply_changes.py", 
            "--input", str(patch_file)
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nReturn code: {result.returncode}"
        
        return templates.TemplateResponse("updota.html", {
            "request": request,
            "output": output,
            "success": result.returncode == 0,
            "patch_content": output
        })
        
    except Exception as e:
        output = f"Erro ao aplicar patch: {str(e)}"
        return templates.TemplateResponse("updota.html", {
            "request": request,
            "output": output,
            "success": False,
            "patch_content": output
        })

@app.get("/_dev/reload")
async def dev_reload():
    """Endpoint para reload de desenvolvimento"""
    reload_file = Path(".reload")
    reload_file.touch()
    return {"status": "reload triggered", "file": str(reload_file)}

@app.post("/updota/stop")
async def stop_server():
    """Para o servidor (uso em desenvolvimento)"""
    try:
        # Criar arquivo de sinal para parar servidor
        stop_file = Path(".stop_server")
        stop_file.touch()
        
        # Responder imediatamente antes de parar
        response_data = {"status": "stopping server", "message": "Servidor sera parado em 2 segundos"}
        
        # Agendar parada do servidor em background
        def delayed_stop():
            import time
            time.sleep(2)
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
        
        threading.Thread(target=delayed_stop).start()
        
        return response_data
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/updota/commit")
async def commit_changes():
    """Faz commit das alteracoes via git"""
    try:
        # TOO/APP/MAIBB - Executar git add
        result_add = subprocess.run(
            ["git", "add", "."], 
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        
        # TOO/APP/MAICC - Executar git commit
        result_commit = subprocess.run([
            "git", "commit", "-m", "[apply_changes] Alteracoes via updota"
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        if result_commit.returncode == 0:
            return {"success": True, "message": "Commit realizado com sucesso"}
        else:
            # Se nao ha nada para commitar, retornar info
            if "nothing to commit" in result_commit.stdout.lower():
                return {"success": False, "message": "Nada para commitar - working tree limpo"}
            else:
                return {"success": False, "message": result_commit.stderr or result_commit.stdout or "Erro desconhecido no commit"}
            
    except Exception as e:
        return {"success": False, "message": f"Erro ao executar git: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)