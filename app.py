
from pathlib import Path
import html
import pandas as pd
import plotly.express as px
import streamlit as st
from emission_engine import *

BASE=Path(__file__).resolve().parent
DATA=BASE/"data"

st.set_page_config(
    page_title="EmberGuard • Crematorium Emissions Screening",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{--ink:#182b3a;--muted:#637789;--line:#dce7ee}
.stApp{background:linear-gradient(180deg,#fffdfb 0%,#eef7f8 100%);color:var(--ink)}
.block-container{max-width:1580px;padding-top:1rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#f3f8f9;border-right:1px solid var(--line)}
[data-testid="stSidebar"] *{color:var(--ink)}
.hero{background:linear-gradient(120deg,#ffffff 0%,#fff5ea 48%,#eefaf8 100%);
border:1px solid var(--line);border-radius:28px;padding:30px 34px;margin-bottom:18px;
box-shadow:0 14px 44px rgba(46,68,78,.07)}
.ey{font-size:.72rem;font-weight:900;letter-spacing:.16em;text-transform:uppercase;color:#eb7b2e}
.hero h1{font-size:2.45rem;line-height:1.02;margin:.35rem 0 .6rem;color:var(--ink)}
.hero p{margin:0;color:var(--muted);font-size:1rem;max-width:1200px}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 8px 25px rgba(24,55,75,.05)}
.lab{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:800}
.kpi{font-size:1.7rem;font-weight:900}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:15px}
</style>
""",unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<div class="ey">LOCAL-FIRST · ENVIRONMENTAL SCREENING · OPERATIONS</div>
<h1>🔥 EmberGuard</h1>
<p>Crematorium Emissions Screening Platform — screens possible emission-risk patterns using fuel use, operating duration, weather dispersion, equipment condition, maintenance records, filtration controls, nearby exposure, and local incident signals.</p>
</div>
""",unsafe_allow_html=True)

@st.cache_data
def load_data():
    return {
        "sites": pd.read_csv(DATA/"sample_crematorium_sites.csv"),
        "history": pd.read_csv(DATA/"sample_emissions_history.csv"),
        "incidents": pd.read_csv(DATA/"sample_emission_incidents.csv"),
    }

d=load_data()
allx=build_emission_screening(d["sites"],d["history"],d["incidents"])

with st.sidebar:
    st.markdown("### EmberGuard controls")
    page=st.radio(
        "Workspace",
        [
            "Emissions Command Center","Site Explorer","Risk Landscape",
            "Fuel & Operations","Equipment & Maintenance","Weather & Exposure",
            "Incident Monitor","Scenario Lab","Data & Export"
        ],
    )
    area=st.selectbox("Focus area",["All"]+sorted(allx.area.unique().tolist()))
    bands=st.multiselect("Risk bands",list(BANDS),default=list(BANDS))
    floor=st.slider("Minimum risk score",0,100,0)
    st.markdown("---")
    st.caption("🟢 Low · 🟡 Moderate · 🟠 High · 🔴 Critical")
    st.markdown("---")
    st.caption("100% local • No external APIs")

s=allx.copy()
if area!="All": s=s[s.area==area]
if bands: s=s[s.risk_band.isin(bands)]
s=s[s.emission_risk_score>=floor].copy()
m=calculate_metrics(s)

if page=="Emissions Command Center":
    st.markdown("## Emissions command center")
    items=[
        ("Sites screened",m["sites"]),("Average risk",f'{m["avg_score"]:.1f}/100'),
        ("High / Critical",m["high_critical"]),("Operational readiness",f'{m["readiness"]:.1f}%'),
        ("Fuel pressure",f'{m["fuel"]:.1f}%'),("Weather constraint",f'{m["weather"]:.1f}%')
    ]
    cols=st.columns(6)
    for c,(label,val) in zip(cols,items):
        c.markdown(f'<div class="card"><div class="lab">{label}</div><div class="kpi">{val}</div></div>',unsafe_allow_html=True)

    l,r=st.columns([1.35,1])
    with l:
        top=s.nlargest(15,"emission_risk_score")
        fig=px.bar(
            top,x="site_id",y="emission_risk_score",color="risk_band",
            hover_data=["site_name","area","top_driver","fuel_use_kg_day","maintenance_gap_days"],
            labels={"site_id":"Site","emission_risk_score":"Screening risk score"}
        )
        fig.update_layout(height=420,margin=dict(l=8,r=8,t=20,b=8))
        st.plotly_chart(fig,use_container_width=True)
    with r:
        q=s.risk_band.value_counts().reindex(list(BANDS),fill_value=0).reset_index()
        q.columns=["risk_band","count"]
        fig=px.pie(q,values="count",names="risk_band",hole=.62)
        fig.update_layout(height=420,margin=dict(l=8,r=8,t=20,b=8))
        st.plotly_chart(fig,use_container_width=True)
    st.markdown("### Area operating picture")
    st.dataframe(build_area_summary(s),use_container_width=True,hide_index=True)

elif page=="Site Explorer":
    st.markdown("## Site Explorer")
    if s.empty:
        st.warning("No sites match the current filters.")
    else:
        sid=st.selectbox("Select crematorium site",s.site_id.tolist())
        r=s.loc[s.site_id==sid].iloc[0]
        a,b,c,e,f=st.columns(5)
        a.metric("Risk",f'{r.emission_risk_score:.1f}/100')
        b.metric("Band",r.risk_band)
        c.metric("Readiness",f'{r.operational_readiness_pct:.0f}%')
        e.metric("Fuel use",f'{r.fuel_use_kg_day:.0f} kg/day')
        f.metric("Top driver",r.top_driver)
        vals={
            "Fuel type":r.fuel_type,"Operating hours":f"{r.operating_hours_day:.1f} h/day",
            "Equipment condition":f"{r.equipment_condition_pct:.0f}%","Maintenance gap":f"{r.maintenance_gap_days:.0f} days",
            "Stack condition":f"{r.stack_condition_pct:.0f}%","Weather dispersion":f"{r.weather_dispersion_pct:.0f}%",
            "Wind speed":f"{r.wind_speed_mps:.1f} m/s","Nearby exposure":f"{r.nearby_exposure_pct:.0f}%",
            "Filter efficiency":f"{r.filter_efficiency_pct:.0f}%","Inspection recency":f"{r.inspection_recency_days:.0f} days"
        }
        l,rr=st.columns(2)
        with l:
            st.dataframe(pd.DataFrame({"Signal":list(vals),"Value":list(vals.values())}),use_container_width=True,hide_index=True)
        with rr:
            for rec in generate_recommendations(r):
                st.markdown(f'<div class="card" style="margin:6px 0">{html.escape(rec)}</div>',unsafe_allow_html=True)
        comp=pd.DataFrame({
            "factor":["Fuel","Operating","Equipment","Maintenance","Stack","Weather","Exposure","Filter","Inspection","Incidents","History"],
            "risk":[r.fuel_component,r.operating_component,r.equipment_component,r.maintenance_component,r.stack_component,r.weather_component,r.exposure_component,r.filter_component,r.inspection_component,r.incident_component,r.historical_component]
        })
        fig=px.bar(comp,x="factor",y="risk",color="factor",text="risk")
        fig.update_traces(texttemplate="%{text:.1f}",textposition="outside")
        fig.update_layout(height=400,showlegend=False)
        st.plotly_chart(fig,use_container_width=True)

elif page=="Risk Landscape":
    st.markdown("## Emission-risk landscape")
    fig=px.scatter(
        s,x="fuel_use_kg_day",y="maintenance_gap_days",size="nearby_exposure_pct",
        color="risk_band",hover_name="site_name",
        hover_data=["area","equipment_condition_pct","weather_dispersion_pct","top_driver"],
        labels={"fuel_use_kg_day":"Fuel use (kg/day)","maintenance_gap_days":"Maintenance gap (days)"}
    )
    fig.update_layout(height=520)
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(
        s.nlargest(25,"emission_risk_score")[["site_id","site_name","area","emission_risk_score","risk_band","top_driver"]],
        use_container_width=True,hide_index=True
    )

elif page=="Fuel & Operations":
    st.markdown("## Fuel & operating profile")
    l,r=st.columns(2)
    with l:
        fig=px.scatter(
            s,x="fuel_use_kg_day",y="operating_hours_day",size="emission_risk_score",
            color="risk_band",hover_name="site_name",
            labels={"fuel_use_kg_day":"Fuel use (kg/day)","operating_hours_day":"Operating hours/day"}
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig,use_container_width=True)
    with r:
        st.dataframe(
            s.nlargest(25,"fuel_component")[
                ["site_id","site_name","fuel_type","fuel_use_kg_day","operating_hours_day","fuel_component","emission_risk_score","risk_band"]
            ],
            use_container_width=True,hide_index=True
        )

elif page=="Equipment & Maintenance":
    st.markdown("## Equipment & maintenance")
    l,r=st.columns(2)
    with l:
        fig=px.scatter(
            s,x="equipment_condition_pct",y="maintenance_gap_days",size="stack_condition_pct",
            color="risk_band",hover_name="site_name",
            labels={"equipment_condition_pct":"Equipment condition %","maintenance_gap_days":"Maintenance gap (days)"}
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig,use_container_width=True)
    with r:
        st.dataframe(
            s.sort_values(["maintenance_gap_days","equipment_condition_pct"],ascending=[False,True])[
                ["site_id","site_name","area","maintenance_gap_days","equipment_condition_pct","stack_condition_pct","filter_efficiency_pct","operational_readiness_pct"]
            ],
            use_container_width=True,hide_index=True
        )

elif page=="Weather & Exposure":
    st.markdown("## Weather dispersion & nearby exposure")
    l,r=st.columns(2)
    with l:
        fig=px.scatter(
            s,x="weather_dispersion_pct",y="nearby_exposure_pct",size="wind_speed_mps",
            color="risk_band",hover_name="site_name",
            labels={"weather_dispersion_pct":"Dispersion index %","nearby_exposure_pct":"Nearby exposure %"}
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig,use_container_width=True)
    with r:
        st.dataframe(
            s.nlargest(25,"weather_component")[
                ["site_id","site_name","area","weather_dispersion_pct","wind_speed_mps","humidity_pct","nearby_exposure_pct","weather_component","emission_risk_score","risk_band"]
            ],
            use_container_width=True,hide_index=True
        )
    st.info("Weather and dispersion signals are screening inputs. They are not a substitute for stack testing, dispersion modelling, or official environmental monitoring.")

elif page=="Incident Monitor":
    st.markdown("## Emission incident monitor")
    ev=d["incidents"].copy()
    if area!="All":
        ev=ev[ev.site_id.isin(s.site_id.tolist())]
    l,r=st.columns(2)
    with l:
        counts=ev.groupby(["severity"],as_index=False).size().rename(columns={"size":"count"})
        fig=px.bar(counts,x="severity",y="count",color="severity",text="count")
        fig.update_layout(height=360)
        st.plotly_chart(fig,use_container_width=True)
    with r:
        st.metric("Logged incidents",len(ev))
        st.metric("Unresolved",int((ev["resolved"].astype(str).str.lower()!="true").sum()))
    st.dataframe(ev,use_container_width=True,hide_index=True)
    st.download_button("Download incident CSV",ev.to_csv(index=False).encode(),"emberguard_incidents.csv","text/csv")

elif page=="Scenario Lab":
    st.markdown("## Scenario Lab")
    st.caption("Planning simulation only — not an emission concentration forecast or compliance determination.")
    c=st.columns(3)
    fuel=c[0].slider("Fuel-use pressure",0,100,45)
    operating=c[1].slider("Operating-duration pressure",0,100,35)
    equipment=c[2].slider("Equipment-condition gap",0,100,30)
    c=st.columns(3)
    maintenance=c[0].slider("Maintenance gap",0,100,30)
    stack=c[1].slider("Stack-condition gap",0,100,25)
    weather=c[2].slider("Weather constraint",0,100,25)
    c=st.columns(4)
    exposure=c[0].slider("Nearby exposure",0,100,25)
    filt=c[1].slider("Filter-control gap",0,100,20)
    insp=c[2].slider("Inspection gap",0,100,15)
    incidents=c[3].slider("Incident pressure",0,100,10)
    score=scenario_score(fuel,operating,equipment,maintenance,stack,weather,exposure,filt,insp,incidents)
    st.markdown(
        f'<div class="card"><div class="lab">Scenario output</div><div class="kpi">{score:.1f}/100</div><div>{classify_score(score)} modeled emission-risk pattern</div></div>',
        unsafe_allow_html=True
    )

else:
    st.markdown("## Data & export")
    tabs=st.tabs(["Screened results","Sites","History","Incidents"])
    with tabs[0]:
        st.dataframe(s,use_container_width=True,hide_index=True)
        st.download_button("Download screened results CSV",s.to_csv(index=False).encode(),"emberguard_screened_results.csv","text/csv")
    with tabs[1]:st.dataframe(d["sites"],use_container_width=True,hide_index=True)
    with tabs[2]:st.dataframe(d["history"],use_container_width=True,hide_index=True)
    with tabs[3]:st.dataframe(d["incidents"],use_container_width=True,hide_index=True)
