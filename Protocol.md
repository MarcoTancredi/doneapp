
# Protocolo Único — ACR (Anchor / Cut / Replace)

## Objetivo
Aplicar mudanças **sem tocar** nas linhas de referência (âncora), localizando o ponto com precisão. A busca da **âncora** tolera linhas em branco **entre** as linhas da âncora. A operação é **sempre por linhas inteiras**.

## Ações suportadas
- **FileNew**  
  Cria/substitui um arquivo com o conteúdo do `Subject`. Se o arquivo existir, o original vai para `.backup/<relpath>.bak-YYYYmmdd-HHMMSS`.

- **FileDelete**  
  Move o arquivo para `.backup/` (backup com timestamp).

- **TextModify** (ACR)  
  Preserva a **ÂNCORA** (se houver), opcionalmente **remove** o trecho `Cut`, e **insere** o `Replace`:
  - `#BeginAnchor ... #EndAnchor` (**opcional**) — linhas “sagradas”; **nunca** são alteradas/removidas. Se omitido, a operação não ancora o ponto e o `Cut` é buscado no arquivo todo.
  - `#BeginCut ... #EndCut` (**opcional, porém obrigatório se não houver âncora**) — sequência de **linhas inteiras** a substituir.
  - `#BeginReplace ... #EndReplace` (**obrigatório**) — linhas a inserir. Sempre gravadas com `\n` no **início** e no **fim** para não “colar”.

### Regras
1. **Âncora imutável**: conteúdos entre `#BeginAnchor/#EndAnchor` **nunca** são tocados.
2. **Localização da âncora**: tolera linhas em branco **entre** as linhas da âncora (não dentro); espaços **dentro** da linha contam.
3. **Cut por linhas inteiras**: sequência de linhas **contíguas**; não fazemos edição “no meio da linha”.
4. **Ordem**:
   - Se **há âncora**: localizar âncora → procurar `Cut` **depois** da âncora; se achar, substituir; se não achar, **inserir Replace** logo após a âncora.
   - Se **não há âncora**: é **obrigatório** haver `Cut`; substituir a **primeira ocorrência** dessa sequência no arquivo.
5. **Backups**: sempre que gravar, cria `.backup/<relpath>.bak-YYYYmmdd-HHMMSS`.
6. **Primeira ocorrência**: atua na **primeira** ocorrência encontrada. Se houver ambiguidade, **forneça mais linhas de âncora** ou um `Cut` mais específico.

## Formatos

### FileNew

#Action: FileNew
#Target: caminho/arquivo.ext
#BeginSubject
…conteúdo do arquivo…
