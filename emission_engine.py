from __future__ import annotations

import numpy as np
import pandas as pd

BANDS = ("Low", "Moderate", "High", "Critical")


def classify_score(score: float) -> str:
    s = float(score)
    if s < 25:
        return "Low"
    if s < 50:
        return "Moderate"
    if s < 75:
        return "High"
    return "Critical"


def validate_inputs(sites: pd.DataFrame, history: pd.DataFrame, incidents: pd.DataFrame) -> None:
    required = {
        "sites": {
            "site_id", "site_name", "area", "fuel_type", "fuel_use_kg_day",
            "operating_hours_day", "equipment_condition_pct", "maintenance_gap_days",
            "stack_condition_pct", "weather_dispersion_pct", "wind_speed_mps",
            "humidity_pct", "nearby_exposure_pct", "filter_efficiency_pct",
            "inspection_recency_days"
        },
        "history": {
            "site_id", "date", "fuel_use_kg_day", "operating_hours_day",
            "equipment_condition_pct", "maintenance_gap_days", "stack_condition_pct",
            "weather_dispersion_pct", "incident_count", "inspection_score_pct"
        },
        "incidents": {
            "incident_id", "site_id", "date", "incident_type", "severity", "resolved"
        },
    }
    frames = {"sites": sites, "history": history, "incidents": incidents}
    errors = []
    for name, needed in required.items():
        missing = sorted(needed - set(frames[name].columns))
        if missing:
            errors.append(f"{name} missing required columns: {', '.join(missing)}")
    if errors:
        raise ValueError("Input validation failed | " + " | ".join(errors))


def _numeric(df: pd.DataFrame, cols: list[str]) -> None:
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)


def build_emission_screening(sites: pd.DataFrame, history: pd.DataFrame, incidents: pd.DataFrame) -> pd.DataFrame:
    validate_inputs(sites, history, incidents)
    s = sites.copy()
    h = history.copy()
    i = incidents.copy()

    _numeric(
        s,
        [
            "fuel_use_kg_day", "operating_hours_day", "equipment_condition_pct",
            "maintenance_gap_days", "stack_condition_pct", "weather_dispersion_pct",
            "wind_speed_mps", "humidity_pct", "nearby_exposure_pct",
            "filter_efficiency_pct", "inspection_recency_days",
        ],
    )
    _numeric(
        h,
        [
            "fuel_use_kg_day", "operating_hours_day", "equipment_condition_pct",
            "maintenance_gap_days", "stack_condition_pct", "weather_dispersion_pct",
            "incident_count", "inspection_score_pct",
        ],
    )

    hist = h.groupby("site_id", as_index=False).agg(
        hist_fuel_use=("fuel_use_kg_day", "mean"),
        hist_operating_hours=("operating_hours_day", "mean"),
        hist_equipment_condition=("equipment_condition_pct", "mean"),
        hist_maintenance_gap=("maintenance_gap_days", "mean"),
        hist_stack_condition=("stack_condition_pct", "mean"),
        hist_dispersion=("weather_dispersion_pct", "mean"),
        hist_incidents=("incident_count", "mean"),
        hist_inspection=("inspection_score_pct", "mean"),
    )

    inc = i.groupby("site_id", as_index=False).agg(
        incident_count=("incident_id", "count"),
        unresolved_incidents=(
            "resolved",
            lambda x: int((x.astype(str).str.lower() != "true").sum()),
        ),
    )

    out = s.merge(hist, on="site_id", how="left").merge(inc, on="site_id", how="left")
    fill_cols = [
        "hist_fuel_use", "hist_operating_hours", "hist_equipment_condition",
        "hist_maintenance_gap", "hist_stack_condition", "hist_dispersion",
        "hist_incidents", "hist_inspection", "incident_count", "unresolved_incidents",
    ]
    for c in fill_cols:
        out[c] = out[c].fillna(0)

    out["fuel_component"] = np.clip(out["fuel_use_kg_day"] / 120 * 100, 0, 100)
    out["operating_component"] = np.clip(out["operating_hours_day"] / 16 * 100, 0, 100)
    out["equipment_component"] = (100 - out["equipment_condition_pct"]).clip(0, 100)
    out["maintenance_component"] = np.clip(out["maintenance_gap_days"] / 90 * 100, 0, 100)
    out["stack_component"] = (100 - out["stack_condition_pct"]).clip(0, 100)
    out["weather_component"] = (100 - out["weather_dispersion_pct"]).clip(0, 100)
    out["exposure_component"] = out["nearby_exposure_pct"].clip(0, 100)
    out["filter_component"] = (100 - out["filter_efficiency_pct"]).clip(0, 100)
    out["inspection_component"] = np.clip(out["inspection_recency_days"] / 180 * 100, 0, 100)
    out["incident_component"] = np.minimum(
        out["incident_count"] * 12 + out["unresolved_incidents"] * 20 + out["hist_incidents"] * 5,
        100,
    )
    out["historical_component"] = np.minimum(
        out["hist_fuel_use"] / 1.5
        + out["hist_operating_hours"] * 2
        + (100 - out["hist_equipment_condition"]) * 0.5
        + out["hist_maintenance_gap"] / 2,
        100,
    )

    out["emission_risk_score"] = (
        out["fuel_component"] * 0.17
        + out["operating_component"] * 0.09
        + out["equipment_component"] * 0.15
        + out["maintenance_component"] * 0.14
        + out["stack_component"] * 0.12
        + out["weather_component"] * 0.10
        + out["exposure_component"] * 0.08
        + out["filter_component"] * 0.07
        + out["inspection_component"] * 0.04
        + out["incident_component"] * 0.02
        + out["historical_component"] * 0.02
    ).clip(0, 100).round(1)

    out["risk_band"] = out["emission_risk_score"].map(classify_score)

    out["operational_readiness_pct"] = (
        100
        - (
            out["equipment_component"] * 0.30
            + out["maintenance_component"] * 0.25
            + out["stack_component"] * 0.20
            + out["filter_component"] * 0.15
            + out["inspection_component"] * 0.10
        )
    ).clip(0, 100).round(1)

    drivers = {
        "fuel_component": "Fuel-use pressure",
        "operating_component": "Operating-duration pressure",
        "equipment_component": "Equipment-condition gap",
        "maintenance_component": "Maintenance gap",
        "stack_component": "Stack-condition gap",
        "weather_component": "Weather-dispersion constraint",
        "exposure_component": "Nearby exposure",
        "filter_component": "Filtration-efficiency gap",
        "inspection_component": "Inspection recency",
        "incident_component": "Incident pressure",
        "historical_component": "Historical signal",
    }
    driver_cols = list(drivers)
    out["top_driver"] = out[driver_cols].idxmax(axis=1).map(drivers)

    return out


def calculate_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "sites": 0,
            "avg_score": 0,
            "high_critical": 0,
            "readiness": 0,
            "fuel": 0,
            "weather": 0,
        }
    return {
        "sites": len(df),
        "avg_score": round(float(df["emission_risk_score"].mean()), 1),
        "high_critical": int(df["risk_band"].isin(["High", "Critical"]).sum()),
        "readiness": round(float(df["operational_readiness_pct"].mean()), 1),
        "fuel": round(float(df["fuel_component"].mean()), 1),
        "weather": round(float(df["weather_component"].mean()), 1),
    }


def build_area_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["area", "sites", "avg_risk", "high_critical", "avg_readiness"]
        )
    out = (
        df.groupby("area", as_index=False)
        .agg(
            sites=("site_id", "count"),
            avg_risk=("emission_risk_score", "mean"),
            high_critical=("risk_band", lambda x: int(x.isin(["High", "Critical"]).sum())),
            avg_readiness=("operational_readiness_pct", "mean"),
        )
        .round(1)
        .sort_values("avg_risk", ascending=False)
    )
    return out


def build_signal_summary(df: pd.DataFrame) -> pd.DataFrame:
    vals = {
        "Fuel use": df["fuel_component"].mean(),
        "Operating duration": df["operating_component"].mean(),
        "Equipment condition": df["equipment_component"].mean(),
        "Maintenance gap": df["maintenance_component"].mean(),
        "Stack condition": df["stack_component"].mean(),
        "Weather dispersion": df["weather_component"].mean(),
        "Nearby exposure": df["exposure_component"].mean(),
        "Filter efficiency": df["filter_component"].mean(),
        "Inspection recency": df["inspection_component"].mean(),
    }
    return pd.DataFrame(
        {"signal": list(vals), "value_pct": [round(float(v), 1) for v in vals.values()]}
    )


def generate_recommendations(row) -> list[str]:
    checks = [
        ("fuel_component", 55, "🔥 Review fuel-use intensity and operating logs."),
        ("operating_component", 55, "⏱️ Review operating duration and scheduling patterns."),
        ("equipment_component", 45, "⚙️ Prioritize equipment-condition inspection."),
        ("maintenance_component", 45, "🛠️ Review maintenance backlog and service history."),
        ("stack_component", 45, "🏭 Inspect stack-condition indicators and records."),
        ("weather_component", 50, "🌬️ Review current dispersion conditions before interpreting emission patterns."),
        ("exposure_component", 50, "🏘️ Review nearby exposure and sensitive-site context."),
        ("filter_component", 40, "🧰 Review filtration/control performance and maintenance."),
        ("inspection_component", 45, "📋 Schedule an inspection review if records are overdue."),
        ("incident_component", 40, "🚨 Review incident history and unresolved events."),
    ]
    recommendations = [msg for key, threshold, msg in checks if float(row[key]) >= threshold]
    return recommendations or ["✅ No dominant elevated screening signal detected. Continue routine monitoring."]


def scenario_score(
    fuel, operating, equipment_gap, maintenance_gap, stack_gap,
    weather_constraint, exposure, filter_gap, inspection_gap, incidents
) -> float:
    score = (
        fuel * 0.17
        + operating * 0.09
        + equipment_gap * 0.15
        + maintenance_gap * 0.14
        + stack_gap * 0.12
        + weather_constraint * 0.10
        + exposure * 0.08
        + filter_gap * 0.07
        + inspection_gap * 0.04
        + incidents * 0.04
    )
    return round(float(np.clip(score, 0, 100)), 1)
