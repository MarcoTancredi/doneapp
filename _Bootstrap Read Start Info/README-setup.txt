README — Setup rápido (Windows 11 24H2)

1) Baixar e executar (Admin) o script PowerShell:
   - Clique com o botão direito em PowerShell e escolha "Executar como Administrador".
   - Rode:
       Set-ExecutionPolicy Bypass -Scope Process -Force
       .\setup_env.ps1

   O que ele faz:
   - Instala Volta (via winget), instala e fixa Node.js 22.18.0, habilita Corepack.
   - Baixa e instala Miniforge (conda-forge), configura mamba, define Python 3.12 no base.
   - Cria o ambiente 'py312' com Python 3.12.

2) Ativar o ambiente Python para trabalhar:
       conda activate py312

3) Rodar o servidor de aplicação de protocolo:
       pip install flask
       python apply_changes.py
   Abra o arquivo updater.html no navegador e aponte para o endpoint (ex.: http://127.0.0.1:5000/apply).

Links úteis (documentação oficial):
- Miniforge releases: https://github.com/conda-forge/miniforge/releases
- Página Miniforge (conda-forge): https://conda-forge.org/miniforge/
- Volta (instalação Windows): https://docs.volta.sh/guide/getting-started
- Volta (detalhes do instalador Windows): https://docs.volta.sh/advanced/installers
- Node 22.18.0 LTS (release notes e artefatos): https://nodejs.org/en/blog/release/v22.18.0
- Corepack (como habilitar): https://nodejs.org/download/release/v22.11.0/docs/api/corepack.html