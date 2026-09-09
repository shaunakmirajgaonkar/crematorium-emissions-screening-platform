# Run instructions
```bash
cd ~/Downloads/CrematoriumEmissionsScreeningPlatform_EmberGuard_Local
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 validate_project.py
python3 -m pytest -q
python3 run.py
```
Open http://localhost:8501.
