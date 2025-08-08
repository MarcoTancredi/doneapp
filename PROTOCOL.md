Ação: Criar

Local: PROTOCOL.md

Código Completo:

PROTOCOLO OFICIAL DE EDIÇÃO — PROJETO DONE



Objetivo

- Permitir que QUALQUER modelo de IA, sem memória prévia, edite o projeto com zero erro humano.

- Nenhum humano altera código manualmente; TODAS as mudanças são aplicadas pelo “aplicador”.



Arquivos de referência

- contexto.txt → resume o projeto e o ambiente

- README.md → como instalar/rodar/fluxo de trabalho

- PROTOCOL.md → este documento (formato das respostas do modelo)

- tools/apply_changes.py → aplicador que cria/modifica arquivos baseado nas respostas do chat



Fluxo de trabalho

1) O humano cola a resposta do chat em inbox/patch_input.txt (ou via interface web /).

2) Executa-se tools/apply_changes.py (ou run_apply.bat).

3) O aplicador cria diretórios/arquivos, inclui/edita trechos usando contexto e gera backup + commit Git.



Formatos de mensagem do modelo (SEMPRE em português)

A) Criar arquivo

# Ação: Criar

# Local: caminho/arquivo.ext

# Código Completo:

<código integral do arquivo>



B) Incluir trecho (arquivo existente)

# Ação: Incluir

# Local: caminho/arquivo.ext

# Contexto Anterior (5 linhas antes da inclusão):

<exatamente 5 linhas existentes antes do ponto de inclusão>

# Código a Incluir:

<linhas a serem adicionadas imediatamente após o contexto anterior>



C) Modificar trecho (arquivo existente)

# Ação: Modificar

# Local: caminho/arquivo.ext

# Contexto Antes (5 linhas anteriores à modificação):

<exatamente 5 linhas anteriores ao bloco a ser substituído>

# Contexto Depois (5 linhas posteriores à modificação):

<exatamente 5 linhas posteriores ao bloco a ser substituído>

# Novo Código:

<novo bloco que substituirá integralmente o conteúdo entre os contextos>



D) Ação de Sistema (opcional; diretórios/arquivos)

# Ação: Sistema

# Operação: CriarDiretorio|DeletarDiretorio|DeletarArquivo

# Alvo: caminho/alvo



Regras de contexto

- Correspondência EXATA das linhas de contexto (inclui espaços e quebras).

- Se não houver match, a operação daquele bloco é abortada e registrada no console.

- Backup automático em ./.backups/AAAAMMDD_HHMMSS/



Comentários de bloco (recomendado)

- Delimite funções com marcadores estáveis:

# ===== INÍCIO [AUTH-LOGIN] =====

…código…

# ===== FIM [AUTH-LOGIN] =====



Git e auditoria

- Cada execução cria commits atômicos por bloco (mensagem: [apply_changes] …).

- Não force-push nem edite manualmente arquivos — use SEMPRE o aplicador.



Interface de colagem

- A rota web GET / exibe um textarea; POST /apply salva em inbox/patch_input.txt.

- Depois, execute run_apply.bat para aplicar.



Fim do protocolo.
