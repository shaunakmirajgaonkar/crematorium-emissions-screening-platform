from pathlib import Path
import pandas as pd
from emission_engine import build_emission_screening,scenario_score,BANDS
D=Path(__file__).resolve().parent/"data"
o=build_emission_screening(
    pd.read_csv(D/"sample_crematorium_sites.csv"),
    pd.read_csv(D/"sample_emissions_history.csv"),
    pd.read_csv(D/"sample_emission_incidents.csv")
)
assert len(o)==24
assert o.emission_risk_score.between(0,100).all()
assert o.operational_readiness_pct.between(0,100).all()
assert set(o.risk_band).issubset(BANDS)
assert 0<=scenario_score(100,100,100,100,100,100,100,100,100,100)<=100
print("PASS: EmberGuard validation")
print(f"Sites: {len(o)}")
print(f"Areas: {o.area.nunique()}")
print(f"Average risk score: {o.emission_risk_score.mean():.1f}")
print(f"High/Critical: {o.risk_band.isin(["High","Critical"]).sum()}")
