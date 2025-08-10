# apply_changes.py — servidor de aplicação do Protocolo (com CORS, backups e Git)
from __future__ import annotations
import os, re, time, json, subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CORS: permitir chamadas do updater.html (file://) para http://localhost:5000 ---
@app.after_request
def add_cors_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    return resp

@app.route('/apply', methods=['OPTIONS'])
def apply_options():
    return ('', 204)

# Estado global do workspace (para backups)
CURRENT_WORKSPACE_ROOT: Optional[Path] = None

ACTION_RE = re.compile(r'^#Action:\s*(FileNew|FileDelete|TextInsert|TextDelete|TextModify)\s*$', re.I)
TARGET_RE = re.compile(r'^#Target:\s*(.+?)\s*$')

def _norm_inside(root: Path, target: str) -> Path:
    p = (root / target).resolve()
    if root not in p.parents and p != root:
        raise ValueError(f"Target escapes workspace: {p}")
    return p

def _read_block(lines: List[str], start_marker: str, end_marker: str) -> Tuple[List[str], int]:
    """Lê bloco incluindo linhas vazias e retorna (conteudo, offset). Se start não encontrado, (-1)."""
    content = []
    i = 0
    while i < len(lines) and lines[i].strip() != start_marker:
        i += 1
    if i == len(lines):
        return [], -1
    i += 1
    while i < len(lines) and lines[i].strip() != end_marker:
        content.append(lines[i].rstrip('\n').rstrip('\r'))
        i += 1
    if i == len(lines):
        raise ValueError(f"Missing {end_marker}")
    i += 1
    return content, i

def _backup_dest(src: Path, root: Optional[Path], ts: str) -> Path:
    """Destino de backup em .backup/ preservando estrutura relativa."""
    if root:
        try:
            rel = src.relative_to(root)
        except Exception:
            rel = Path(src.name)
        base = root / ".backup" / rel
    else:
        base = src.parent / ".backup" / src.name
    base.parent.mkdir(parents=True, exist_ok=True)
    return base.with_name(base.name + f".bak-{ts}")

def _wrap_subject(subject: str) -> str:
    """Garante CR no início e no fim do subject."""
    s = subject
    if not s.startswith('\n'):
        s = '\n' + s
    if not s.endswith('\n'):
        s = s + '\n'
    return s

def _anchor_to_pattern(anchor_lines: List[str]) -> str:
    """
    Constrói um regex que ignora linhas em branco entre as linhas de âncora.
    Concatena as linhas NÃO vazias com um separador que admite múltiplas quebras.
    """
    nonblank = [ln for ln in anchor_lines if ln.strip() != ""]
    if not nonblank:
        # âncora vazia: casa com vazio
        return r""
    # Entre cada linha da âncora, permitir qualquer quantidade de linhas em branco/whitespace
    sep = r"(?:[ \t]*\r?\n[ \t]*)*"
    parts = [re.escape(ln) for ln in nonblank]
    return "(" + sep.join(parts) + ")"

def _apply_one_action(action: str, file_path: Path, blocks: List[dict]) -> str:
    log = []
    ts = time.strftime("%Y%m%d-%H%M%S")
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if action == "FileNew":
        if file_path.exists():
            backup = _backup_dest(file_path, CURRENT_WORKSPACE_ROOT, ts)
            file_path.replace(backup)
            log.append(f"Backup existente: {backup}")
        subject = "\n".join(blocks[0]["subject"]) if blocks else ""
        subject = _wrap_subject(subject)
        file_path.write_text(subject, encoding="utf-8")
        return "\n".join(log + [f"FileNew OK: {file_path}"])

    if action == "FileDelete":
        if file_path.exists():
            backup = _backup_dest(file_path, CURRENT_WORKSPACE_ROOT, ts)
            file_path.replace(backup)
            log.append(f"Backup: {backup}")
            return "\n".join(log + [f"FileDelete OK (arquivo movido para backup)"])
        else:
            return "\n".join(log + [f"FileDelete: arquivo não existe ({file_path})"])

    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado para ação {action}: {file_path}")

    original = file_path.read_text(encoding="utf-8")
    new_text = original

    for idx, blk in enumerate(blocks, start=1):
        before_lines = blk["before"]
        after_lines  = blk["after"]
        subject      = _wrap_subject("\n".join(blk["subject"]))
        before_pat   = _anchor_to_pattern(before_lines)
        after_pat    = _anchor_to_pattern(after_lines)

        # Captura âncoras originais como grupos 1 e 3 para preservá-las literalmente
        pattern = re.compile(before_pat + r"(.*?)" + after_pat, re.DOTALL)
        m = pattern.search(new_text)
        if not m:
            log.append(f"[NÃO ACHADO] Bloco {idx}: {subject[:80]}")
            continue

        g_before = m.group(1)
        g_after  = m.group(3) if m.lastindex and m.lastindex >= 3 else m.group(m.lastindex)  # suporte se só 2 grupos
        if action == "TextInsert":
            replacement = g_before + subject + g_after
        elif action == "TextDelete":
            replacement = g_before + g_after
        elif action == "TextModify":
            replacement = g_before + subject + g_after
        else:
            raise ValueError(f"Ação não suportada: {action}")

        new_text = new_text[:m.start()] + replacement + new_text[m.end():]
        log.append(f"[OK] Bloco {idx}: {subject.strip()[:80]}")

    if new_text != original:
        backup = _backup_dest(file_path, CURRENT_WORKSPACE_ROOT, ts)
        backup.write_text(original, encoding="utf-8")
        file_path.write_text(new_text, encoding="utf-8")
        log.append(f"Backup do original: {backup}")
    else:
        log.append("Nenhuma alteração aplicada (âncoras não encontradas).")

    return "\n".join(log)

def parse_protocol(proto_text: str):
    lines = [ln.rstrip("\r\n") for ln in proto_text.splitlines()]
    i = 0
    actions = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        m = ACTION_RE.match(line)
        if m:
            action = m.group(1)
            i += 1
            if i >= len(lines) or not TARGET_RE.match(lines[i].strip()):
                raise ValueError("Esperado '#Target:' após '#Action:'")
            target = TARGET_RE.match(lines[i].strip()).group(1)
            i += 1
            blocks = []
            while i < len(lines):
                if lines[i].strip() == "#ActionEnded":
                    i += 1
                    break
                remaining = lines[i:]
                before, offset = _read_block(remaining, "#BeginBeforeLines", "#EndBeforeLines")
                if offset == -1:
                    break
                i += offset
                # ActionText é opcional
                if i < len(lines) and lines[i].strip() == "#BeginActionText":
                    _, off2 = _read_block(lines[i:], "#BeginActionText", "#EndActionText")
                    i += off2
                after, off3 = _read_block(lines[i:], "#BeginAfterLines", "#EndAfterLines")
                i += off3
                subject, off4 = _read_block(lines[i:], "#BeginSubject", "#EndSubject")
                i += off4
                blocks.append({"before": before, "after": after, "subject": subject})
            actions.append({"action": action, "target": target, "blocks": blocks})
        else:
            i += 1
    return actions

@app.get("/status")
def status():
    # conda ok?
    conda_ok = bool(_which("conda"))
    # git inited?
    git_inited = False
    if CURRENT_WORKSPACE_ROOT and (CURRENT_WORKSPACE_ROOT / ".git").exists():
        git_inited = True
    return jsonify({"ok": True, "server":"on", "conda_ok": conda_ok, "git_inited": git_inited})

def _which(cmd: str) -> Optional[str]:
    from shutil import which
    return which(cmd)

def _run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git"]+args, cwd=str(cwd), text=True, capture_output=True, shell=False)

@app.post("/git/init")
def git_init():
    data = request.get_json(force=True)
    root = Path(data.get("workspace_root",".")).resolve()
    name = data.get("name")
    email= data.get("email")
    if not name or not email:
        return jsonify({"ok":False,"error":"name/email are required"}), 400
    (root / ".gitignore").parent.mkdir(parents=True, exist_ok=True)
    r1 = _run_git(["init"], root)
    if r1.returncode != 0:
        return jsonify({"ok":False,"error":r1.stderr}), 500
    _run_git(["config","user.name",name], root)
    _run_git(["config","user.email",email], root)
    return jsonify({"ok":True,"output":r1.stdout})

@app.post("/git/commit")
def git_commit():
    data = request.get_json(force=True)
    root = Path(data.get("workspace_root",".")).resolve()
    message = data.get("message","update")
    do_push = bool(data.get("push", False))
    r_add = _run_git(["add","-A"], root)
    if r_add.returncode != 0:
        return jsonify({"ok":False,"error":r_add.stderr}), 500
    r_c = _run_git(["commit","-m",message], root)
    out = r_add.stdout + "\n" + r_c.stdout
    if r_c.returncode != 0:
        return jsonify({"ok":False,"error":r_c.stderr, "output":out}), 500
    if do_push:
        r_remote = _run_git(["remote"], root)
        if r_remote.stdout.strip():
            r_p = _run_git(["push"], root)
            out += "\n" + r_p.stdout
            if r_p.returncode != 0:
                return jsonify({"ok":False,"error":r_p.stderr, "output":out}), 500
        else:
            out += "\n(no remote configured; skipping push)"
    return jsonify({"ok":True,"output":out})

@app.post("/restart")
def restart():
    # Sai do processo; dev.ps1/dev.bat relançam
    os._exit(0)

@app.post("/apply")
def apply_changes():
    data = request.get_json(force=True)
    workspace_root = Path(data.get("workspace_root", ".")).resolve()
    protocol_text = data.get("protocol_text", "")
    out_lines = []

    global CURRENT_WORKSPACE_ROOT
    CURRENT_WORKSPACE_ROOT = workspace_root

    actions = parse_protocol(protocol_text)
    for a in actions:
        action = a["action"]
        target = a["target"]
        out_lines.append(f"=> Log/print Action File Inicio: {action} {target}")
        try:
            file_path = _norm_inside(workspace_root, target)
            result = _apply_one_action(action, file_path, a["blocks"])
            out_lines.append(result)
        except Exception as e:
            out_lines.append(f"[ERRO] {e}")
        out_lines.append("")
    out = "\n".join(out_lines) if out_lines else "Nada aplicado."
    return jsonify({"ok": True, "output": out})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()
    print(f"* Servindo em http://{args.host}:{args.port}  (POST /apply)")
    app.run(host=args.host, port=args.port)
    