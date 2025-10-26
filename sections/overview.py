# sections/overview.py
import streamlit as st
import pandas as pd
import altair as alt
import re
from typing import Iterable

# ===== Utilities =====
def _coerce_year(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df

def _filter_years(df: pd.DataFrame, y0: int | None, y1: int | None) -> pd.DataFrame:
    if df is None or df.empty or "year" not in df.columns or y0 is None or y1 is None:
        return df
    return df[(df["year"] >= y0) & (df["year"] <= y1)]

def _filter_countries(df: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    if df is None or df.empty or "country" not in df.columns or not countries:
        return df
    return df[df["country"].isin(countries)]

def _mortality_under50(df_mortality: pd.DataFrame) -> pd.DataFrame:
    if df_mortality is None or df_mortality.empty or "age" not in df_mortality.columns:
        return df_mortality
    m = df_mortality.copy()
    age = m["age"].astype(str)
    mask = (
        age.str.contains("Y_LT", case=False)
        | age.str.contains(r"Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49", regex=True, case=False)
        | age.eq("TOTAL")
    )
    return m[mask]

def _styled_chart(chart, title=None, height=340):
    return (
        chart.properties(
            title=title or "",
            width="container",
            height=height,
            background="white",
            padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        )
        .configure_view(stroke="lightgray", strokeWidth=1.2)
        .configure_axis(grid=False, domainColor="lightgray", labelColor="#333", titleColor="#333")
        .configure_title(anchor="start", fontSize=14, color="#222", fontWeight="bold")
    )

# ===== Render =====
def render_overview(
    df_screening: pd.DataFrame | None = None,
    df_mortality: pd.DataFrame | None = None,
    df_exam_income: pd.DataFrame | None = None,
) -> None:
    st.subheader("Overview")

    df_screening = _coerce_year(df_screening)
    df_mortality  = _coerce_year(df_mortality)
    df_exam_income = _coerce_year(df_exam_income)

    # ---- read global filters from app.py ----
    gf = st.session_state.get("global_filters", {}) or {}
    countries = gf.get("countries", ["FR"])
    y0, y1 = gf.get("y0"), gf.get("y1")

    # Apply filters
    df_screening_f = _filter_years(_filter_countries(df_screening, countries), y0, y1)
    df_mortality_f = _filter_years(_filter_countries(df_mortality, countries), y0, y1)
    df_exam_income_f = _filter_years(_filter_countries(df_exam_income, countries), y0, y1)

    # ===== KPIs =====
    k1, k2, k3 = st.columns(3)

    scr_kpi = scr_delta = ""
    if not df_screening_f.empty and {"screening_rate", "year"}.issubset(df_screening_f.columns):
        last_year = df_screening_f["year"].dropna().max()
        first_year = df_screening_f["year"].dropna().min()
        latest = df_screening_f[df_screening_f["year"].eq(last_year)]
        base = df_screening_f[df_screening_f["year"].eq(first_year)]
        if not latest.empty:
            scr_kpi = f"{latest['screening_rate'].median():.1f}"
        if not latest.empty and not base.empty:
            scr_delta = f"{latest['screening_rate'].median() - base['screening_rate'].median():+.1f} vs {first_year}"
    k1.metric("Organized screening median (latest year)", scr_kpi, scr_delta)

    mort_kpi = mort_delta = ""
    mort_sub = _mortality_under50(df_mortality_f)
    if mort_sub is not None and not mort_sub.empty and {"mortality_rate", "year"}.issubset(mort_sub.columns):
        explicit = mort_sub[mort_sub["age"].astype(str) != "TOTAL"] if "age" in mort_sub.columns else mort_sub
        chosen = explicit if not explicit.empty else mort_sub
        last_year_m = chosen["year"].dropna().max()
        first_year_m = chosen["year"].dropna().min()
        latest_m = chosen[chosen["year"].eq(last_year_m)]
        base_m = chosen[chosen["year"].eq(first_year_m)]
        if not latest_m.empty:
            mort_kpi = f"{latest_m['mortality_rate'].median():.1f}"
        if not latest_m.empty and not base_m.empty:
            mort_delta = f"{latest_m['mortality_rate'].median() - base_m['mortality_rate'].median():+.1f} vs {first_year_m}"
    k2.metric("Mortality median under 50 (per 100k, latest)", mort_kpi, mort_delta)

    # Income gap Q5 − Q1 under 50 (latest survey year)
    gap_val = gap_note = ""
    ei = df_exam_income_f.copy()
    if not ei.empty and {"income_quintile","exam_rate","year"}.issubset(ei.columns):
        qcol = ei["income_quintile"].astype(str).str.upper()
        ei.loc[qcol.str.match(r"^QU([1-5])$"), "income_quintile"] = "Q" + qcol.str.extract(r"^QU([1-5])$")[0]
        last_year_e = ei["year"].dropna().max()
        e_last = ei[ei["year"].eq(last_year_e)]
        if not e_last.empty:
            q5 = e_last[e_last["income_quintile"].eq("Q5")]["exam_rate"].median()
            q1 = e_last[e_last["income_quintile"].eq("Q1")]["exam_rate"].median()
            if pd.notna(q5) and pd.notna(q1):
                gap_val = f"{(q5 - q1):.1f} pp"
                gap_note = f"Year {int(last_year_e)}"
    k3.metric("Income gap in last X-ray exam (<50): Q5 − Q1", gap_val, gap_note)

    st.markdown("---")

    # ===== Screening trend =====
    st.markdown("#### Screening participation over time")
    if not df_screening_f.empty and {"screening_rate", "year", "country"}.issubset(df_screening_f.columns):
        scr_ts = (
            df_screening_f.groupby(["country", "year"], as_index=False)["screening_rate"].mean()
            .sort_values(["country", "year"])
        )
        line = (
            alt.Chart(scr_ts)
            .mark_line(point=True)
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y("screening_rate:Q", title="Organized screening rate (%)"),
                color=alt.Color("country:N", title="Country"),
                tooltip=["country", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
            )
        )
        st.altair_chart(_styled_chart(line), use_container_width=True)
    else:
        st.info("Screening table not available or missing screening_rate.")

    # ===== Mortality trend =====
    st.markdown("#### Mortality trend (female C50)")
    if mort_sub is not None and not mort_sub.empty and {"mortality_rate", "year", "country"}.issubset(mort_sub.columns):
        chart_df = mort_sub[mort_sub.get("age", "").astype(str) != "TOTAL"] if "age" in mort_sub.columns else mort_sub
        if chart_df.empty:
            chart_df = mort_sub
        mort_ts = (
            chart_df.groupby(["country", "year"], as_index=False)["mortality_rate"].mean()
            .sort_values(["country", "year"])
        )
        line = (
            alt.Chart(mort_ts)
            .mark_line(point=True)
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y("mortality_rate:Q", title="Deaths per 100k, under 50 preferred"),
                color=alt.Color("country:N", title="Country"),
                tooltip=["country", "year", alt.Tooltip("mortality_rate:Q", format=".1f")],
            )
        )
        st.altair_chart(_styled_chart(line), use_container_width=True)
    else:
        st.info("Mortality table not available or missing mortality_rate.")
