import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# --------------------------------------------------------------------------------------
# Configuração básica
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
STATIC_DIR = BASE_DIR / "static"
LAST_SUMMARY_FILE = BASE_DIR / ".last_updota_summary.txt"

app = FastAPI(title="DroneApp")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------
def _norm_lf(text: str) -> str:
    # Garante LF e remove BOM indesejado
    return text.replace("\r\n", "\n").replace("\r", "\n")

def _parse_updota_script(script: str):
    """
    Formato esperado mínimo:
      # Ação: Criar
      # Local: caminho/arquivo.ext
      # A partir daqui, conteúdo completo do arquivo (UTF-8, LF)
      ...
    Retorna: (acao:str, local:Path, conteudo:str, resumo:str)
    """
    lines = _norm_lf(script).split("\n")

    acao: Optional[str] = None
    local: Optional[str] = None
    content_start_idx: Optional[int] = None

    for i, line in enumerate(lines):
        L = line.strip()
        if L.lower().startswith("# ação:") or L.lower().startswith("# acao:"):
            acao = L.split(":", 1)[1].strip()
        elif L.lower().startswith("# local:"):
            local = L.split(":", 1)[1].strip()
        elif L.lower().startswith("# a partir daqui"):
            content_start_idx = i + 1
            break

    if not acao or not local:
        raise ValueError("Script incompleto: precisa de '# Ação:' e '# Local:'.")

    if content_start_idx is None:
        # se não achar o marcador, considera tudo após as duas primeiras diretivas
        # encontra a primeira linha vazia após as diretivas
        after_headers = 0
        header_count = 0
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("# ação:") or line.strip().lower().startswith("# acao:"):
                header_count += 1
            elif line.strip().lower().startswith("# local:"):
                header_count += 1
            if header_count >= 2 and line.strip() == "":
                after_headers = i + 1
                break
        content_start_idx = after_headers

    conteudo = "\n".join(lines[content_start_idx:]) if content_start_idx is not None else ""
    conteudo = _norm_lf(conteudo)
    if conteudo.strip() == "":
        # Evita criar arquivo vazio por engano
        raise ValueError("Conteúdo do arquivo vazio. Verifique o texto após o cabeçalho.")

    resumo = f"{acao} -> {local}"
    return acao, local, conteudo, resumo

def _write_utf8_lf(full_path: Path, content: str):
    full_path.parent.mkdir(parents=True, exist_ok=True)
    # newline='\n' garante LF; encoding utf-8 sem BOM
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_norm_lf(content))

def _git(cmd_args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + cmd_args,
        cwd=str(cwd or BASE_DIR),
        capture_output=True,
        text=True,
        shell=False,
    )

def _commit_and_push(message: str):
    _git(["add", "-A"])
    commit = _git(["commit", "-m", message])
    # Se não houver mudanças, git sai com código diferente — tratamos como ok
    push = _git(["push"])
    return commit, push

def _exec_if_exists(candidates):
    """
    Tenta rodar um script externo (restart/stop) se existir.
    Retorna (bool executou, caminho_usado ou None).
    """
    for p in candidates:
        pth = Path(p)
        if pth.exists():
            # Execução não-bloqueante
            try:
                if pth.suffix.lower() == ".bat":
                    subprocess.Popen([str(pth)], cwd=str(pth.parent), creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([str(pth)], cwd=str(pth.parent))
                return True, str(pth)
            except Exception:
                pass
    return False, None


# --------------------------------------------------------------------------------------
# Rotas públicas simples (mantém compatibilidade visual com seus templates)
# --------------------------------------------------------------------------------------
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/cadastro")
def cadastro_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})


# --------------------------------------------------------------------------------------
# /updota (GET/POST) — 1 textarea, sem links de Login/Cadastro; botões: Salvar+Aplicar, Limpar,
# Restart Server, Stop Server, Commit Changes
# --------------------------------------------------------------------------------------
@app.api_route("/updota", methods=["GET", "POST"])
async def updota(request: Request,
                 script: Optional[str] = Form(None),
                 op: Optional[str] = Form(None)):
    status_msg = ""
    last_summary = LAST_SUMMARY_FILE.read_text(encoding="utf-8").strip() if LAST_SUMMARY_FILE.exists() else ""

    if request.method == "POST":
        try:
            if op == "clear":
                # Apenas volta a página sem script e sem apagar arquivo nenhum
                return templates.TemplateResponse("updota.html", {
                    "request": request,
                    "script": "",
                    "status_msg": "Buffer limpo (não alterei arquivos no disco).",
                    "last_summary": last_summary,
                })

            elif op == "save_apply":
                acao, local, conteudo, resumo = _parse_updota_script(script or "")
                destino = (BASE_DIR / local).resolve()

                # Proteção: mantém dentro do projeto
                if not str(destino).startswith(str(BASE_DIR)):
                    raise ValueError("Caminho inválido fora do repositório.")

                # Ação mínima: Criar/Substituir conteúdo
                _write_utf8_lf(destino, conteudo)

                # Guarda resumo para uso no commit subsequente
                LAST_SUMMARY_FILE.write_text(resumo, encoding="utf-8", newline="\n")
                last_summary = resumo

                status_msg = f"OK: {resumo}"
                return templates.TemplateResponse("updota.html", {
                    "request": request,
                    "script": script or "",
                    "status_msg": status_msg,
                    "last_summary": last_summary,
                })

            elif op == "commit_changes":
                msg = last_summary if last_summary else "updota: commit"
                commit, push = _commit_and_push(msg)
                status_msg = "Commit e push executados."
                # Inclui pedaços de saída para debug rápido
                status_msg += f"\ncommit: {commit.returncode} {commit.stderr.strip() or commit.stdout.strip()}"
                status_msg += f"\npush:   {push.returncode} {push.stderr.strip() or push.stdout.strip()}"
                return templates.TemplateResponse("updota.html", {
                    "request": request,
                    "script": script or "",
                    "status_msg": status_msg,
                    "last_summary": last_summary,
                })

            else:
                # botão desconhecido
                return templates.TemplateResponse("updota.html", {
                    "request": request,
                    "script": script or "",
                    "status_msg": "Nenhuma operação válida foi selecionada.",
                    "last_summary": last_summary,
                })

        except Exception as e:
            return templates.TemplateResponse("updota.html", {
                "request": request,
                "script": script or "",
                "status_msg": f"ERRO: {type(e).__name__}: {str(e)}",
                "last_summary": last_summary,
            })

    # GET
    return templates.TemplateResponse("updota.html", {
        "request": request,
        "script": "",
        "status_msg": "",
        "last_summary": last_summary,
    })


# --------------------------------------------------------------------------------------
# Restart / Stop — tentam rodar scripts externos se existirem; caso contrário, apenas informam.
# Você pode colocar, por exemplo:
#   scripts/restart_server.bat   (Windows)
#   scripts/stop_server.bat
# --------------------------------------------------------------------------------------
@app.post("/admin/restart")
def admin_restart():
    executed, path_used = _exec_if_exists([
        BASE_DIR / "scripts" / "restart_server.bat",
        BASE_DIR / "restart_server.bat",
        BASE_DIR / "scripts" / "restart_server.sh",
    ])
    if executed:
        return JSONResponse({"ok": True, "msg": f"Restart acionado via {path_used}."})
    # fallback: cria uma 'flag' para watcher externo
    (BASE_DIR / "RESTART.MARK").write_text("restart", encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "Flag RESTART.MARK criada. Reinicie o servidor manualmente se necessário."})

@app.post("/admin/stop")
def admin_stop():
    executed, path_used = _exec_if_exists([
        BASE_DIR / "scripts" / "stop_server.bat",
        BASE_DIR / "stop_server.bat",
        BASE_DIR / "scripts" / "stop_server.sh",
    ])
    if executed:
        return JSONResponse({"ok": True, "msg": f"Stop acionado via {path_used}."})
    (BASE_DIR / "STOP.MARK").write_text("stop", encoding="utf-8")
    return JSONResponse({"ok": True, "msg": "Flag STOP.MARK criada. Pare o processo manualmente se necessário."})