import pandas as pd
from emission_engine import *
def load():
    D="data"
    return (
        pd.read_csv(f"{D}/sample_crematorium_sites.csv"),
        pd.read_csv(f"{D}/sample_emissions_history.csv"),
        pd.read_csv(f"{D}/sample_emission_incidents.csv")
    )
def test_bands():
    assert classify_score(0)=="Low"
    assert classify_score(25)=="Moderate"
    assert classify_score(50)=="High"
    assert classify_score(75)=="Critical"
def test_screening():
    s,h,i=load()
    o=build_emission_screening(s,h,i)
    assert len(o)==24
    assert o.emission_risk_score.between(0,100).all()
    assert o.operational_readiness_pct.between(0,100).all()
    assert o.top_driver.notna().all()
def test_scenario_bounds():
    assert 0<=scenario_score(100,100,100,100,100,100,100,100,100,100)<=100
def test_missing_column_rejected():
    s,h,i=load()
    s=s.drop(columns=["fuel_use_kg_day"])
    try:
        build_emission_screening(s,h,i)
    except ValueError as e:
        assert "fuel_use_kg_day" in str(e)
    else:
        raise AssertionError("Expected validation error")
