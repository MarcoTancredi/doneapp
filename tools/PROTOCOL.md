
# Protocolo de Atualização de Arquivos

## Ações
- **FileNew**: cria/replace arquivo com o conteúdo do `Subject`. Se já existir, move o antigo para `.backup/`.
- **FileDelete**: remove (move para `.backup/`) o arquivo alvo.
- **TextInsert**: insere `Subject` **entre** `Before` e `After` (âncoras).
- **TextDelete**: remove a região **entre** `Before` e `After`.
- **TextModify**: substitui a região **entre** `Before` e `After` por `Subject`.

## Regras das Âncoras
- As âncoras são os blocos **Between**:
  - `#BeginBeforeLines` ... `#EndBeforeLines`
  - `#BeginAfterLines` ... `#EndAfterLines`
- **NUNCA** alteramos âncoras no arquivo.
- **Ignoramos linhas em branco** quando localizamos âncoras. Pode haver linhas em branco extras no arquivo que o match ainda ocorre.
- Use o mesmo texto (mesmas linhas) do arquivo como âncora; espaços dentro da linha importam.

## Inserções/Modificações
- Todo `Subject` é gravado com **CR antes e CR depois** (linhas em branco no início e fim).
- Não é necessário `ActionText` (pode ficar vazio). O parser zera variáveis a cada bloco.

## Endpoints REST (servidor)
- `GET /status`: `{ server: "on", conda_ok: bool, git_inited: bool }`
- `POST /restart`: força saída do processo (o **runner** relança).
- `POST /git/init`: body `{ name, email }` → `git init` + `git config`.
- `POST /git/commit`: body `{ message, push?: true }` → `git add -A && git commit -m ...` e **push** se remoto existir e `push=true`.

## Estrutura sugerida
/ (raiz)
updater.bat
/tools
updater.html
apply_changes.py
dev.ps1
dev.bat
/.backup
/src …


