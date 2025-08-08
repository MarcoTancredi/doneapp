#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

ENC = "utf-8"

HEADER_RE = re.compile(r"^#\s*A[cç]ão:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
LOCAL_RE  = re.compile(r"^#\s*Local:\s*(.+)$", re.MULTILINE | re.IGNORECASE)

# Marcador para conteúdo completo
FULL_CONTENT_RE = re.compile(
    r"^#\s*A partir daqui,\s*conte[úu]do completo do arquivo.*?$",
    re.IGNORECASE | re.MULTILINE
)

# Bloco Antes/Depois
ANTES_RE = re.compile(r"^#\s*Antes:\s*$", re.IGNORECASE | re.MULTILINE)
DEPOIS_RE = re.compile(r"^#\s*Depois:\s*$", re.IGNORECASE | re.MULTILINE)

def read_text(p: Path) -> str:
    return p.read_text(encoding=ENC, errors="replace") if p.exists() else ""

def write_text(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    # força LF
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    p.write_text(content, encoding=ENC, newline="\n")

def apply_full_content(local: Path, patch: str) -> None:
    # Captura tudo após a linha "A partir daqui, conteúdo completo do arquivo..."
    m = FULL_CONTENT_RE.search(patch)
    if not m:
        raise RuntimeError("Marcador de conteúdo completo não encontrado.")
    start = m.end()
    content = patch[start:].lstrip("\n")
    # NÃO escrever arquivo vazio por engano:
    if content.strip() == "":
        raise RuntimeError("Conteúdo após o marcador está vazio.")
    write_text(local, content)

def apply_antes_depois(local: Path, patch: str) -> None:
    # Divide em seções
    m_antes = ANTES_RE.search(patch)
    m_depois = DEPOIS_RE.search(patch)
    if not m_antes or not m_depois or m_depois.end() <= m_antes.end():
        raise RuntimeError("Blocos # Antes / # Depois inválidos ou ausentes.")
    antes = patch[m_antes.end():m_depois.start()].lstrip("\n")
    depois = patch[m_depois.end():].lstrip("\n")

    original = read_text(local)
    if antes not in original:
        raise RuntimeError("Contexto Antes não encontrado no arquivo alvo.")
    new_content = original.replace(antes, depois)
    write_text(local, new_content)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Caminho do patch_input.txt")
    args = ap.parse_args()

    inbox = Path(args.input)
    patch = read_text(inbox)
    if not patch.strip():
        print("[ERRO] patch_input.txt está vazio.")
        raise SystemExit(2)

    m_action = HEADER_RE.search(patch)
    m_local  = LOCAL_RE.search(patch)
    if not m_action or not m_local:
        print("[ERRO] Cabeçalho inválido. Use '# Ação:' e '# Local:'.")
        raise SystemExit(2)

    action = m_action.group(1).strip().lower()
    local_rel = m_local.group(1).strip()
    target = Path(local_rel)

    try:
        if "criar" in action or "create" in action:
            apply_full_content(target, patch)
            print(f"[OK] Criado: {target}")
        elif "substituir" in action or "replace" in action:
            apply_full_content(target, patch)
            print(f"[OK] Substituído: {target}")
        elif "editar" in action or "update" in action or "alterar" in action or "modificar" in action:
            apply_antes_depois(target, patch)
            print(f"[OK] Editado: {target}")
        else:
            # fallback: tenta full-content
            apply_full_content(target, patch)
            print(f"[OK] Aplicado (full): {target}")
    except Exception as e:
        print(f"[FALHA] {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()