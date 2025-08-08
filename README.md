Ação: Criar

Local: README.md

Código Completo:

DONE — Setup Inicial (do zero)

1) Clonar o repositório
git clone https://github.com/SEU_USUARIO/SEU_REPO.git
cd SEU_REPO


2) Criar ambiente (Conda)

Opção A (environment.yml):
conda env create -f environment.yml
conda activate doneapp

Opção B (manual):
conda create -n doneapp python=3.12
conda activate doneapp
pip install -r requirements.txt   # se existir


3) Executar servidor (interface “colar e aplicar”)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Abra http://localhost:8000 → cole a resposta do chat e clique em Salvar Patch.
O arquivo será salvo em inbox/patch_input.txt.


4) Aplicar alterações do patch
	•	Windows:
	•	Dê 2 cliques em run_apply.bat ou
	•	conda activate doneapp e python tools/apply_changes.py --input inbox/patch_input.txt
	•	O aplicador cria diretórios/arquivos, modifica trechos com contexto, faz backup em .backups/ e gera commit Git.


5) Ordem de leitura para QUALQUER MODELO
	1.	Leia contexto.txt
	2.	Leia PROTOCOL.md
	3.	Analise a árvore do repositório
	4.	Responda usando os blocos “Ação: …” do PROTOCOL.md


6) Estrutura mínima
inbox/
  patch_input.txt   # entrada do chat
tools/
  apply_changes.py  # aplicador
app/
  main.py           # FastAPI mínimo (UI de colar e aplicar)
  templates/
    index.html      # Textarea e botão “Salvar Patch”
.backups/           # criado pelo aplicador


7) Próximos passos
	•	Aprovar estética Neon das 2 telas iniciais (landing + cadastro)
	•	Implementar backend de cadastro, verificação e login (YouTube OAuth)
	•	Definir SMTP (Hostinger/Gmail) e estratégia de WhatsApp/SMS com menor custo

