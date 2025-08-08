# Ação: Criar
# Local: AI_BOOTSTRAP.md
# A partir daqui, conteúdo completo do arquivo (UTF-8, LF)

# AI_BOOTSTRAP — Como qualquer IA deve continuar este projeto (START HERE)

> Leia este arquivo **primeiro**. Em seguida, leia `contexto.txt` e `PROTOCOL.md`.  
> Todas as alterações de código **devem** ser entregues no formato de patch descrito em `PROTOCOL.md` e aplicadas via **/updota** (ou `tools/apply_changes.py`).

---

## 1) Resumo do projeto
- App web em **Python 3.12** + **FastAPI**.
- Foco: módulos de cadastro/login, UI Neon responsiva, e utilitário **/updota** para aplicar patches do próprio chat.
- Baixo custo: sem Docker por enquanto; dependências mínimas (vide `requirements.txt`).
- Hospedagem atual: máquina Windows 11 local (IP dinâmico) com **Cloudflare Tunnel** (Zero Trust). Migração futura: **VPS (HostGator)** → **AWS/Azure**.
- Mídias serão servidas pelo provedor (HostGator) quando entrarmos em publicação multi-redes.

Rotas principais:
- `/` → redireciona para `/login`
- `/login` → tela de login (UI Neon, responsiva, botões sociais YouTube/TikTok/GitHub/Facebook)
- `/cadastro` → tela de cadastro (checklist de métodos de autenticação)
- `/updota` → colar patch; salvar; aplicar; ver saída (uso apenas por admin)

---

## 2) Onde a IA precisa olhar antes de responder
1. **Este arquivo**: `AI_BOOTSTRAP.md`
2. **Contexto de ambiente**: `contexto.txt`
3. **Protocolo de patches**: `PROTOCOL.md`
4. **Estrutura do app**: `app/main.py`, `app/templates/*.html`, `tools/apply_changes.py`, `requirements.txt`
5. **Notas do repositório**: `README.md`

Se algum destes arquivos estiver ausente/desatualizado, **a IA deve propor um patch de criação/correção** (no formato do `PROTOCOL.md`) antes de qualquer outra mudança.

---

## 3) Regras de formatação para a IA (obrigatórias)
- Responder **somente** com blocos de código contendo patches no formato do `PROTOCOL.md`.  
  Nada de texto fora de bloco quando a intenção for alterar/crear arquivos.
- **ASCII puro**: sem aspas “curvas”, travessão, reticências especiais, etc. Use `"` `'` `--` `...`.
- **UTF-8**; quebras de linha **LF**.
- Para **Criar** arquivos: conteúdo completo a partir da 3ª linha.
- Para **Modificar**: forneça `# Antes:` (até ~5–20 linhas que identifiquem com segurança o trecho) e `# Depois:` com o novo conteúdo. Evite contexto frágil.

---

## 4) Como aplicar patches
Opção A — via UI:
- Acesse **/updota**
- Cole o patch
- Clique **Salvar Patch e Aplicar**
- Verifique o output (sucesso/erros)

Opção B — via CLI (Windows):
conda activate doneapp
python tools\apply_changes.py –input inbox\patch_input.txt

Depois:
git add .
git commit -m “[apply_changes] <descrição>”
git push

---

## 5) Executar localmente

conda activate doneapp
uvicorn app.main:app –reload –host 0.0.0.0 –port 8000

Acesse:  
- `http://127.0.0.1:8000/login`  
- `http://127.0.0.1:8000/cadastro`  
- `http://127.0.0.1:8000/updota`

---

## 6) Convenções de UI e feedback ao usuário
- Mensagens inline (sem pop-ups).  
  - Sucesso: texto verde por **1s**  
  - Erro/Em implementação: texto vermelho por **3s**  
- Valores (cores/duração) virão de config futura (arquivo/tabela).  
- Layout mobile-first (9:16), estilos **Neon** e sensação de “janela flutuando”.

---

## 7) Próximos passos (roadmap curto)
- Finalizar/estabilizar UI de `/login` e `/cadastro`.
- Implementar backend de cadastro + verificação por e-mail (gratis/baixo custo) e **log** completo.
- Estruturar DB inicial (users, log, config) conforme escopo.
- Login Social: começar por **YouTube**; outros botões exibem “em implementação” (vermelho 3s).
- Preparar migração para VPS e depois cloud.

---

## 8) Erros comuns e como evitar
- **Aspas curvas**: sempre use ASCII.
- **Contexto frágil no patch**: escolha linhas “âncora” robustas no `# Antes:`.
- **Alterar README/PROTOCOL com “Modificar” sem contexto**: prefira “Criar” novos docs ou substituição completa somente se houver consenso/backup.

---

## 9) Contatos e domínios (resumo do contexto.txt)
- Domínio base: `planetamicro.com.br`
- Subdomínios Cloudflare Tunnel já usados (ex.): `app.planetamicro.com.br`, `api.planetamicro.com.br`, `done.planetamicro.com.br`
- Ambiente local Windows 11; Git; Miniconda; VSCode.

---

## 10) O que a IA deve fazer ao iniciar uma nova sessão
1. Ler `AI_BOOTSTRAP.md`, `contexto.txt`, `PROTOCOL.md`.
2. Inspecionar as telas (`app/templates`) e `app/main.py`.
3. Propor patches **no formato do PROTOCOL**.  
4. Nunca enviar instruções “em texto corrido” que precisem ser copiadas manualmente para arquivos.

Fim.