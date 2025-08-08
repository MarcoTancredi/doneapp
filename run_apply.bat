@echo off
SETLOCAL ENABLEEXTENSIONS
REM Atalho para aplicar patches vindos do chat
CALL conda activate doneapp
python tools/apply_changes.py –input “inbox\patch_input.txt”
echo.
echo ==== FINALIZADO. VERIFIQUE ‘Arquivos alterados/criados’ acima. ====
PAUSE