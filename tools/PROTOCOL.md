# Protocolo Único — ACR (Anchor / Cut / Replace)

## Objetivo
Aplicar mudanças **sem tocar** nas linhas de referência (âncora), localizando o ponto com precisão. A âncora tolera **linhas em branco entre as suas linhas**. A operação é **sempre por linhas inteiras** (nunca edita “dentro da linha”).

## Ações suportadas
- **FileNew**  
  Cria/substitui um arquivo com o conteúdo do `Subject`. Se o arquivo existir, o original vai para `.backup/<relpath>.bak-YYYYmmdd-HHMMSS`.

- **FileDelete**  
  Move o arquivo para `.backup/` (backup com timestamp).

- **TextModify** (formato ACR)  
  Preserva a **ÂNCORA** (se houver), opcionalmente **remove** o trecho `Cut`, e **insere** o `Replace`:
  - `#BeginAnchor ... #EndAnchor` (**opcional**) — linhas “sagradas”; **nunca** alteradas/removidas. Se omitido, a operação não ancora o ponto e o `Cut` é buscado no arquivo todo.
  - `#BeginCut ... #EndCut` (**opcional**, **obrigatório se não houver âncora**) — sequência de **linhas inteiras contíguas** a substituir.
  - `#BeginReplace ... #EndReplace` (**obrigatório**) — linhas novas, **gravadas com `\n` no início e no fim** para não “colar”.

### Regras
1. **Âncora imutável**: conteúdos entre `#BeginAnchor/#EndAnchor` **nunca** são tocados.
2. **Localização da âncora**: ignora linhas em branco **entre** as linhas da âncora (não dentro delas). Espaços **dentro** da linha contam.
3. **Cut por linhas inteiras**: substitui **sequência contígua** de linhas — nunca altera “meio de linha”.
4. **Ordem**  
   - Com **Âncora**: localizar âncora → procurar `Cut` **após** a âncora; se achar, substituir; se não achar, **inserir Replace** logo após a âncora.  
   - Sem **Âncora**: `Cut` é **obrigatório**; substitui a **primeira ocorrência global** dessa sequência.
5. **Backups**: antes de gravar, salva o original em `.backup/<relpath>.bak-YYYYmmdd-HHMMSS`.
6. **Primeira ocorrência**: atua na **primeira** ocorrência. Se houver ambiguidade, forneça **mais linhas de âncora** ou um `Cut` mais específico.

## Formatos

### FileNew


#Action: FileNew
#Target: caminho/arquivo.ext
#BeginSubject
…conteúdo do arquivo…
#EndSubject
#ActionEnded

### FileDelete

#Action: FileDelete
#Target: caminho/arquivo.ext
#ActionEnded

### TextModify (ACR)

#Action: TextModify
#Target: caminho/arquivo.ext
#BeginAnchor
…linhas de âncora (opcional; sagradas)…
#EndAnchor
#BeginCut
…linhas a substituir (opcional; obrigatório se não houver âncora)…
#EndCut
#BeginReplace
…linhas novas (gravadas com \n no início e no fim)…
#EndReplace
#ActionEnded

## Exemplos

**Cut sem âncora (linha única e única no arquivo)**  
Trocar `Devolucao = 50` por `Devolucao = 20`:

#Action: TextModify
#Target: regras.txt
#BeginCut
Devolucao = 50
#EndCut
#BeginReplace
Devolucao = 20
#EndReplace
#ActionEnded

**Âncora + Cut**  
Ancorar no trecho “Joao detestou e chamou a policia” e trocar só o `Devolucao = 100` daquele bloco:

#Action: TextModify
#Target: regras.txt
#BeginAnchor
Joao detestou e chamou a policia
#EndAnchor
#BeginCut
Devolucao = 100
#EndCut
#BeginReplace
Devolucao = 1000
#EndReplace
#ActionEnded

**Só Âncora (inserção logo após)**  

#Action: TextModify
#Target: main.txt
#BeginAnchor
Linha de referencia
#EndAnchor
#BeginReplace
NOVO BLOCO
#EndReplace
#ActionEnded

