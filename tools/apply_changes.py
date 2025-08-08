import argparse
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ENC = “utf-8”

HEADER_RE = re.compile(r”^# Ação:\s*(.+)$”, re.MULTILINE)
LOCAL_RE = re.compile(r”^# Local:\s*(.+)$”, re.MULTILINE)

def read_text(p: Path) -> str:
return p.read_text(encoding=ENC) if p.exists() else “”

def write_text(p: Path, content: str):
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(content, encoding=ENC)

def now_stamp():
return dt.datetime.now().strftime(”%Y%m%d_%H%M%S”)

def sha256(data: bytes) -> str:
return hashlib.sha256(data).hexdigest()[:12]

def backup_file(src: Path, backups_root: Path) -> Path:
ts = now_stamp()
folder = backups_root / ts
folder.mkdir(parents=True, exist_ok=True)
dst = folder / src.as_posix().replace(”/”, “__”)
if src.exists():
shutil.copy2(src, dst)
return dst

def git_available() -> bool:
try:
subprocess.run([“git”, “–version”], capture_output=True, check=True)
return True
except Exception:
return False

def git_commit(files, msg: str):
if not git_available():
return
try:
subprocess.run([“git”, “add”, *[str(f) for f in files]], check=True)
subprocess.run([“git”, “commit”, “-m”, msg], check=True)
except subprocess.CalledProcessError:
pass

def extract_blocks(raw: str):
blocks = []
for match in HEADER_RE.finditer(raw):
start = match.start()
next_match = HEADER_RE.search(raw, match.end())
end = next_match.start() if next_match else len(raw)
block_text = raw[start:end].strip()
if LOCAL_RE.search(block_text):
blocks.append(block_text)
return blocks

def get_field(block: str, label: str) -> str:
pattern = re.compile(rf”^# {label}:\s*(.+)$”, re.MULTILINE)
m = pattern.search(block)
if not m:
raise ValueError(f”Campo obrigatório ausente: # {label}:”)
return m.group(1).strip()

def get_section(block: str, title: str) -> str:
header = re.compile(rf”^# {re.escape(title)}:\s*$”, re.MULTILINE)
m = header.search(block)
if not m:
return “”
start = m.end()
next_marker = re.compile(r”^# [A-ZÁ-Úa-zá-ú].*?:”, re.MULTILINE).search(block, start)
end = next_marker.start() if next_marker else len(block)
return block[start:end].lstrip(”\r\n”)

def ensure_repo_root():
return Path.cwd()

def apply_create(local_path: Path, full_code: str, backups_root: Path):
if local_path.exists():
backup_file(local_path, backups_root)
write_text(local_path, full_code)

def find_with_context(haystack: str, context_lines: list[str]) -> int:
context_str = “\n”.join(context_lines).rstrip(”\n”)
return haystack.find(context_str)

def apply_include(local_path: Path, ctx_before: str, to_include: str, backups_root: Path):
if not local_path.exists():
raise FileNotFoundError(f”Arquivo não encontrado para inclusão: {local_path}”)
original = read_text(local_path)
before_lines = [l.rstrip(”\n”) for l in ctx_before.splitlines()]
idx = find_with_context(original, before_lines)
if idx < 0:
raise ValueError(f”Contexto Anterior não encontrado em {local_path}”)
insert_pos = idx + len(”\n”.join(before_lines))
needs_nl = False
if insert_pos < len(original) and original[insert_pos] != “\n”:
needs_nl = True
backup_file(local_path, backups_root)
new_content = original[:insert_pos] + (”\n” if not needs_nl else “”) + to_include + original[insert_pos:]
write_text(local_path, new_content)

def apply_modify(local_path: Path, ctx_before: str, ctx_after: str, new_code: str, backups_root: Path):
if not local_path.exists():
raise FileNotFoundError(f”Arquivo não encontrado para modificação: {local_path}”)
original = read_text(local_path)
before_lines = [l.rstrip(”\n”) for l in ctx_before.splitlines()]
after_lines  = [l.rstrip(”\n”) for l in ctx_after.splitlines()]
idx_before = find_with_context(original, before_lines)
if idx_before < 0:
raise ValueError(f”Contexto Antes não encontrado em {local_path}”)
start_of_replacement = idx_before + len(”\n”.join(before_lines))
remaining = original[start_of_replacement:]
idx_after_rel = find_with_context(remaining, after_lines)
if idx_after_rel < 0:
raise ValueError(f”Contexto Depois não encontrado em {local_path}”)
end_of_replacement = start_of_replacement + idx_after_rel
backup_file(local_path, backups_root)
new_content = original[:start_of_replacement] + “\n” + new_code.rstrip(”\n”) + “\n” + original[end_of_replacement:]
write_text(local_path, new_content)

def apply_system(op: str, target: str, backups_root: Path):
p = Path(target)
if op == “CriarDiretorio”:
p.mkdir(parents=True, exist_ok=True)
elif op == “DeletarDiretorio”:
if p.exists():
backup_dir = backups_root / f”dir_{p.as_posix().replace(’/’,’__’)}_{now_stamp()}”
shutil.make_archive(str(backup_dir), “zip”, p)
shutil.rmtree(p)
elif op == “DeletarArquivo”:
if p.exists():
backup_file(p, backups_root)
p.unlink()
else:
raise ValueError(f”Operação de sistema desconhecida: {op}”)

def process_block(block: str, repo_root: Path, backups_root: Path) -> list[Path]:
changed = []
acao = get_field(block, “Ação”)
if acao.lower().startswith(“criar”):
local = get_field(block, “Local”)
code = get_section(block, “Código Completo”)
fp = repo_root / local
apply_create(fp, code, backups_root)
changed.append(fp)
msg = f”Criar: {local}”
elif acao.lower().startswith(“incluir”):
local = get_field(block, “Local”)
ctx_before = get_section(block, “Contexto Anterior (5 linhas antes da inclusão)”)
code_inc = get_section(block, “Código a Incluir”)
fp = repo_root / local
apply_include(fp, ctx_before, code_inc, backups_root)
changed.append(fp)
msg = f”Incluir em: {local}”
elif acao.lower().startswith(“modificar”):
local = get_field(block, “Local”)
ctx_before = get_section(block, “Contexto Antes (5 linhas anteriores à modificação)”)
ctx_after  = get_section(block, “Contexto Depois (5 linhas posteriores à modificação)”)
new_code   = get_section(block, “Novo Código”)
fp = repo_root / local
apply_modify(fp, ctx_before, ctx_after, new_code, backups_root)
changed.append(fp)
msg = f”Modificar: {local}”
elif acao.lower().startswith(“sistema”):
op = get_field(block, “Operação”)
target = get_field(block, “Alvo”)
apply_system(op, target, backups_root)
msg = f”Sistema: {op} -> {target}”
else:
raise ValueError(f”Ação desconhecida: {acao}”)
git_commit(changed, f”[apply_changes] {msg}”)
return changed

def main():
ap = argparse.ArgumentParser(description=“Aplicador de mudanças a partir do protocolo do Projeto Done.”)
ap.add_argument(”–input”, “-i”, default=“inbox/patch_input.txt”, help=“Arquivo de entrada copiado do chat”)
ap.add_argument(”–repo”, “-r”, default=”.”, help=“Raiz do projeto (repositório)”)
ap.add_argument(”–backups”, “-b”, default=”.backups”, help=“Diretório de backups”)
args = ap.parse_args()
repo_root = Path(args.repo).resolve()
backups_root = (repo_root / args.backups).resolve()
input_path = (repo_root / args.input).resolve()
if not input_path.exists():
print(f”[ERRO] Arquivo de entrada não encontrado: {input_path}”)
sys.exit(1)
raw = read_text(input_path)
blocks = extract_blocks(raw)
if not blocks:
print(”[ERRO] Nenhum bloco válido encontrado (# Ação / # Local).”)
sys.exit(2)
changed_all = []
errors = []
for idx, block in enumerate(blocks, start=1):
try:
changed = process_block(block, repo_root, backups_root)
changed_all.extend(changed)
print(f”[OK] Bloco {idx} aplicado.”)
except Exception as e:
errors.append((idx, str(e)))
print(f”[FALHA] Bloco {idx}: {e}”)
if errors:
print(”\nResumo de falhas:”)
for n, msg in errors:
print(f” - Bloco {n}: {msg}”)
sys.exit(3)
uniq = sorted({str(p.relative_to(repo_root)) for p in changed_all})
if uniq:
print(”\nArquivos alterados/criados:”)
for f in uniq:
print(f” - {f}”)
print(”\nConcluído com sucesso.”)

if name == “main”:
main()