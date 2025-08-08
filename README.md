# DONE — App base (FastAPI + UI de Patch)

## Clonar e preparar
```bash
git clone https://github.com/MarcoTancredi/doneapp.git
cd doneapp
# opção A (conda via environment.yml)
conda env create -f environment.yml
conda activate doneapp
# opção B (manual)
conda create -n doneapp python=3.12 -y
conda activate doneapp
pip install -r requirements.txt