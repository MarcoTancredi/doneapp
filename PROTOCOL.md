# PROTOCOL.md — Protocolo de Resposta e Aplicação de Patches

Este repositório usa **dois modos** de atualização:
1) **Substituição direta**: quando o assistente envia o **arquivo inteiro** em bloco de código.  
2) **Patch estruturado**: quando o assistente envia blocos seguindo o cabeçalho **Ação/Local/…** abaixo. Esses blocos são colados em `/updota` e aplicados por `tools/apply_changes.py`.

> Se houver divergência, **o GitHub é a fonte da verdade**. Antes de aplicar novos patches, sempre faça `git pull`.

---

## Formato do PATCH (para usar via /updota)
Ação: Criar|Modificar

Local: caminho/relativo/do/arquivo.ext

Se Modificar: Contexto Antes (5 linhas)

<exatamente 5 linhas que antecedem o trecho>

Se Modificar: Contexto Depois (5 linhas)

<exatamente 5 linhas que sucedem o trecho>

Código Completo: (se Criar) | Código Novo: (se Modificar)

<conteúdo>
**Regras:**
- Use **aspas normais** (`'` ou `"`) e **hífens duplos** `--` em comandos; não use aspas tipográficas (“ ”) nem travessões (–).
- Para **Modificar**, o aplicador encontra o bloco pelo par **Contexto Antes/Depois** e **substitui integralmente** o conteúdo entre eles.
- O aplicador cria backup automático em `.backups/AAAA-MM-DD_HHMMSS/…` e mostra o relatório no final.

---

## Ordem de leitura para qualquer modelo (ZERO CONTEXTO)

1. Ler `Contexto.txt`
2. Ler `PROTOCOL.md` (este arquivo)
3. Ler `README.md` (passo‑a‑passo)
4. Analisar árvore do repositório (`app/`, `tools/`, `inbox/`)
5. **Responder** sempre usando **Substituição direta** (arquivo inteiro) **ou** o **formato de PATCH** acima.

