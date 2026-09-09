# EmberGuard — Crematorium Emissions Screening Platform

100% local-first Streamlit dashboard for screening possible emission-risk patterns from fuel use, operating duration, weather dispersion, equipment condition, maintenance, filtration controls, nearby exposure, inspections, and incident signals.

## Run on macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 validate_project.py
python3 -m pytest -q
python3 run.py
```
Open http://localhost:8501.

All sample records are synthetic. This platform is a screening aid, not an emissions measurement, dispersion model, compliance determination, or official environmental assessment.
