# Projeto Social Master — Bootstrap de Contexto (leitura obrigatória para IA com memória zero)



Este repositório contém o app web em FastAPI (Python 3.12) com UI Neon, rotas:

- `/` login (User Name / e-mail + senha; social buttons placeholder)

- `/cadastro` cadastro mobile-first

- `/home` pós-login com engrenagem fixa (configurações)

- `/config` placeholder de configurações

- `/updota` módulo para colar/aplicar patches (usa `tools/apply_changes.py`)



## Como a IA deve operar (sempre):

1) Ler **BOOTSTRAP.md**, `README.md`, `PROTOCOL.md` e `app/config/ui.json`.

2) Gerar alterações SEMPRE no formato do `PROTOCOL.md` e o humano colará em `inbox/patch_input.txt`.

3) A aplicação das mudanças será feita pela rota `/updota` (ou `run_apply.bat`). O aplicador faz backup automático em `.backups/`.



## Ambiente de execução

- Windows 11 24H2, Conda Python 3.12 (ver `environment.yml` ou `requirements.txt`).

- Servidor local (rede) para testes em iPhone: