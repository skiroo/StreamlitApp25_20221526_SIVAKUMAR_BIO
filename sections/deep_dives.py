# sections/deep_dives.py — rebuilt from scratch for narrative-first, original visuals
# Author: Kiroshan SIVAKUMAR (EFREI Paris)
# Purpose: Deep-dive analyses aligned to the project storyline
# Tabs:
#  1) Screening: Are we screening enough — and early enough?
#  2) Burden shift: Is the burden shifting to younger women?
#  3) Inequality: Who gets screened — and who doesn’t?
#  4) Correlation Lab: Does screening relate to mortality?
#  5) Europe Maps: Choropleth & Bubble map (toggle)
#  6) Country Profiler: Small multiples + download

from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import re

try:
    import plotly.express as px
    _HAS_PLOTLY = True
except Exception:  # pragma: no cover
    _HAS_PLOTLY = False

# --------------------------------------------------------------------------------------
# Utilities: robust column normalization so this works with either raw or cleaned tables
# --------------------------------------------------------------------------------------

def _normalize_screening(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    # Accept both raw and cleaned
    rename = {
        "geo": "country",
        "TIME_PERIOD": "year",
        "OBS_VALUE": "screening_rate",
        "age": "age",  # may exist in some versions
    }
    d = d.rename(columns={k: v for k, v in rename.items() if k in d.columns})
    # Filter logical columns if available
    if "icd10" in d.columns:
        d = d[d["icd10"].astype(str).str.upper().eq("C50")]
    if "source" in d.columns:
        d = d[d["source"].astype(str).str.upper().eq("PRG")]  # organized programmes only
    # Types
    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    if "screening_rate" in d.columns:
        d["screening_rate"] = pd.to_numeric(d["screening_rate"], errors="coerce")
    return d


def _normalize_mortality(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    rename = {"geo": "country", "TIME_PERIOD": "year", "OBS_VALUE": "mortality_rate"}
    d = d.rename(columns={k: v for k, v in rename.items() if k in d.columns})
    # keep females & breast cancer when present
    if "sex" in d.columns:
        d = d[d["sex"].astype(str).str.upper().str.contains("F", na=False)]
    if "icd10" in d.columns:
        d = d[d["icd10"].astype(str).str.upper().str.contains("C50", na=False)]
    # types
    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    if "mortality_rate" in d.columns:
        d["mortality_rate"] = pd.to_numeric(d["mortality_rate"], errors="coerce")
    return d


def _normalize_income(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    rename = {
        "geo": "country",
        "TIME_PERIOD": "year",
        "OBS_VALUE": "exam_rate",
        "quant_inc": "income_quintile",
        "age": "age_group",
    }
    d = d.rename(columns={k: v for k, v in rename.items() if k in d.columns})
    # canonicalize quintiles to Q1..Q5
    def _canon_quintile(val):
        if pd.isna(val):
            return None
        s = str(val).strip().upper()
        m = re.match(r"^Q(U)?([1-5])$", s)
        if m:
            return f"Q{m.group(2)}"
        if re.fullmatch(r"[1-5]", s):
            return f"Q{s}"
        if "LOW" in s or "FIRST" in s or "BOTTOM" in s:
            return "Q1"
        if "SECOND" in s:
            return "Q2"
        if "THIRD" in s:
            return "Q3"
        if "FOURTH" in s:
            return "Q4"
        if "HIGH" in s or "FIFTH" in s or "TOP" in s:
            return "Q5"
        return None

    if "income_quintile" in d.columns:
        d["income_quintile"] = d["income_quintile"].apply(_canon_quintile)
    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    if "exam_rate" in d.columns:
        d["exam_rate"] = pd.to_numeric(d["exam_rate"], errors="coerce")
    return d


# Age-band helpers used in narrative 40–49 vs 50–69
_AGE40_49_RX = re.compile(r"\b(40-49|40-44|45-49|Y40-49|Y40-44|Y45-49)\b", re.I)
_AGE50_69_RX = re.compile(r"\b(50-69|50-59|60-69|Y50-69|Y50-59|Y60-69)\b", re.I)


def _band_4049(s: str) -> bool:
    return bool(_AGE40_49_RX.search(str(s)))


def _band_5069(s: str) -> bool:
    return bool(_AGE50_69_RX.search(str(s)))


# ISO-2 → ISO-3 (enough for Eurostat/Europe scope)
_ISO2_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","HR":"HRV","CY":"CYP","CZ":"CZE","DK":"DNK","EE":"EST","FI":"FIN","FR":"FRA",
    "DE":"DEU","EL":"GRC","GR":"GRC","HU":"HUN","IE":"IRL","IT":"ITA","LV":"LVA","LT":"LTU","LU":"LUX","MT":"MLT",
    "NL":"NLD","PL":"POL","PT":"PRT","RO":"ROU","SK":"SVK","SI":"SVN","ES":"ESP","SE":"SWE","IS":"ISL","NO":"NOR",
    "CH":"CHE","UK":"GBR","GB":"GBR","AL":"ALB","BA":"BIH","ME":"MNE","MK":"MKD","RS":"SRB","MD":"MDA","UA":"UKR",
    "BY":"BLR"
}


# ---------------------------- Styling helpers -----------------------------------------

def _styled(chart: alt.Chart, title: str = "", height: int | None = None):
    base = chart.properties(title=title, width="container")
    if height:
        base = base.properties(height=height)
    return (
        base
        .configure_view(stroke="#e6e6e6", strokeWidth=1)
        .configure_title(anchor="start", fontSize=14, color="#1e1e1e", fontWeight="bold")
        .configure_axis(grid=False, domainColor="#f3a1c0", labelColor="#333", titleColor="#333")
        .configure_legend(titleColor="#333", labelColor="#333")
    )


# ------------------------------ Main entry --------------------------------------------

def render_deep_dives(
    df_screening: pd.DataFrame | None = None,
    df_mortality: pd.DataFrame | None = None,
    df_exam_income: pd.DataFrame | None = None,
) -> None:
    """Deep dives aligned with the narrative. Original interactive visuals with variations."""

    st.subheader("Deep Dives")
    st.caption("Use the left sidebar to pick countries, years, and map/correlation options.")

    # Normalize
    scr = _normalize_screening(df_screening)
    mort = _normalize_mortality(df_mortality)
    inc = _normalize_income(df_exam_income)

    # Year bounds & sidebar filters
    def _years(df):
        return pd.to_numeric(df.get("year", pd.Series(dtype="Int64")), errors="coerce").dropna()

    y_min = int(min([_years(x).min() for x in [scr, mort, inc] if not x.empty], default=2000))
    y_max = int(max([_years(x).max() for x in [scr, mort, inc] if not x.empty], default=2021))

    all_countries = sorted({
        *scr.get("country", pd.Series([], dtype=str)).dropna().unique().tolist(),
        *mort.get("country", pd.Series([], dtype=str)).dropna().unique().tolist(),
        *inc.get("country", pd.Series([], dtype=str)).dropna().unique().tolist(),
    })

    with st.sidebar:
        st.markdown("### Deep-dive filters")
        primary = st.selectbox("Primary country", all_countries or [""], index=0 if all_countries else 0)
        peers = st.multiselect("Compare with…", [c for c in all_countries if c != primary])
        if y_min <= y_max:
            y0, y1 = st.slider("Year range", y_min, y_max, (y_min, y_max))
        else:
            y0, y1 = None, None

        st.markdown("---")
        st.markdown("**Map type**")
        map_kind = st.radio("", ["Choropleth", "Bubble map"], index=0, horizontal=True)
        st.markdown("**Correlation window**")
        corr_year = st.selectbox("Correlation year", list(range(y_min, y_max + 1))[::-1], index=0)

    sel_countries = [c for c in [primary] + peers if c]

    # Filter by years & countries
    def _sub(df):
        if df is None or df.empty:
            return df
        out = df.copy()
        if y0 is not None:
            out = out[(out["year"] >= y0) & (out["year"] <= y1)]
        if sel_countries:
            out = out[out["country"].isin(sel_countries)]
        return out

    scr_f, mort_f, inc_f = _sub(scr), _sub(mort), _sub(inc)

    # Chips row
    chips = " ".join([f"<span class='chip'>{c}</span>" for c in sel_countries]) if sel_countries else ""
    st.markdown(
        """
        <style>
        .chip {display:inline-block;padding:0.18rem 0.55rem;margin:0 0.25rem 0.35rem 0;border-radius:999px;
               background:rgba(255,105,180,0.12);border:1px solid rgba(255,105,180,0.35);font-size:0.85rem}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if chips:
        st.markdown(chips, unsafe_allow_html=True)

    # Tabs
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "Screening: Early vs Recommended",
        "Burden shift: Under‑50",
        "Inequality: Income × Age",
        "Correlation Lab",
        "Europe Maps",
        "Country Profiler",
    ])

    # ------------------------------------- Tab 1 -------------------------------------
    with t1:
        st.markdown("#### Are we screening enough — and early enough?")
        st.markdown("**Key insight:** Compare age bands 40–49 vs 50–69 to see whether early screening is catching up.")

        # If screening has an age column we honor bands; otherwise show overall trend
        if not scr_f.empty:
            s = scr_f.copy()
            if "age" in s.columns:
                s["age"] = s["age"].astype(str)
                s["band"] = None
                s.loc[s["age"].apply(_band_4049), "band"] = "40–49"
                s.loc[s["age"].apply(_band_5069), "band"] = "50–69"
                s = s.dropna(subset=["band"])
                if not s.empty:
                    ts = (
                        s.groupby(["country", "year", "band"], as_index=False)["screening_rate"].median()
                        .sort_values(["country", "band", "year"])
                    )
                    color = alt.Color("band:N", legend=alt.Legend(title="Age band"))
                    line = alt.Chart(ts).mark_line(point=True).encode(
                        x=alt.X("year:O", title="Year"),
                        y=alt.Y("screening_rate:Q", title="Organized screening rate (%)"),
                        color=color,
                        tooltip=["country", "band", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
                    )
                    st.altair_chart(_styled(line, height=360), use_container_width=True)

                    # KPI: average gap 50–69 minus 40–49 on the latest year available
                    latest_y = int(ts["year"].max())
                    wide = ts[ts["year"].eq(latest_y)].pivot(index=["country"], columns="band", values="screening_rate")
                    if {"50–69", "40–49"}.issubset(wide.columns):
                        gap = (wide["50–69"] - wide["40–49"]).mean()
                        st.metric("Avg gap (50–69 vs 40–49)", f"{gap:.1f} pp", f"Year {latest_y}")
                else:
                    st.info("Age-specific screening bands not available in this selection.")
            else:
                ts = (
                    s.groupby(["country", "year"], as_index=False)["screening_rate"].median()
                    .sort_values(["country", "year"])
                )
                line = alt.Chart(ts).mark_line(point=True).encode(
                    x=alt.X("year:O"), y=alt.Y("screening_rate:Q", title="Organized screening rate (%)"), color="country:N",
                    tooltip=["country", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
                )
                st.altair_chart(_styled(line, height=360), use_container_width=True)
        else:
            st.info("Screening data unavailable for current filters.")

    # ------------------------------------- Tab 2 -------------------------------------
    with t2:
        st.markdown("#### Is the burden shifting to younger women?")
        st.markdown("**Key insight:** Track the share of mortality occurring under 50.")
        if not mort_f.empty and {"mortality_rate", "age", "year", "country"}.issubset(mort_f.columns):
            m = mort_f.copy()
            m["age"] = m["age"].astype(str)
            under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
            total = m[m["age"].eq("TOTAL")]
            if not under.empty and not total.empty:
                u = under.groupby(["country", "year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate": "mort_u50"})
                t = total.groupby(["country", "year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate": "mort_total"})
                merged = pd.merge(u, t, on=["country", "year"], how="inner")
                merged["share_u50"] = (merged["mort_u50"] / merged["mort_total"]) * 100

                # Interactive area/line with hover highlight
                select_country = alt.selection_point(fields=["country"], bind="legend")
                base = alt.Chart(merged).encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("share_u50:Q", title="Share of deaths under 50 (%)"),
                    color=alt.condition(select_country, alt.Color("country:N", title="Country"), alt.value("#d3d3d3")),
                    tooltip=["country", "year", alt.Tooltip("share_u50:Q", format=".1f")],
                )
                area = base.mark_line(point=True).add_params(select_country)
                st.altair_chart(_styled(area, height=360), use_container_width=True)

                # KPI latest average
                latest_y = int(merged["year"].max())
                latest_share = merged.loc[merged["year"].eq(latest_y), "share_u50"].mean()
                st.metric("Avg share under 50", f"{latest_share:.1f}%", f"Year {latest_y}")
            else:
                st.info("Need both age-specific under‑50 and TOTAL mortality to compute the share.")
        else:
            st.info("Mortality data incomplete for this analysis.")

    # ------------------------------------- Tab 3 -------------------------------------
    with t3:
        st.markdown("#### Who gets screened — and who doesn’t?")
        st.markdown("**Key insight:** Younger and lower‑income women report fewer exams.")
        if not inc_f.empty and {"country", "year", "age_group", "income_quintile", "exam_rate"}.issubset(inc_f.columns):
            last_y = int(inc_f["year"].dropna().max())
            e = inc_f[inc_f["year"].eq(last_y)].copy()
            st.caption(f"Latest survey year available: {last_y}")
            if sel_countries:
                default_country = sel_countries[0]
            else:
                default_country = e["country"].iloc[0]
            c_heat = st.selectbox("Select country for heatmap", sorted(e["country"].unique().tolist()), index=sorted(e["country"].unique()).index(default_country))
            ec = e[e["country"].eq(c_heat)]
            if not ec.empty:
                age_order = sorted(ec["age_group"].astype(str).unique().tolist(), key=lambda s: (len(s), s))
                quint_order = ["Q1", "Q2", "Q3", "Q4", "Q5"]
                heat = (
                    alt.Chart(ec)
                    .mark_rect()
                    .encode(
                        x=alt.X("income_quintile:N", sort=quint_order, title="Income quintile"),
                        y=alt.Y("age_group:N", sort=age_order, title="Age group"),
                        color=alt.Color("exam_rate:Q", title="Exam rate (%)", scale=alt.Scale(scheme="reds")),
                        tooltip=["country", "income_quintile", "age_group", alt.Tooltip("exam_rate:Q", format=".1f")],
                    )
                )
                st.altair_chart(_styled(heat, height=max(260, 18 * max(8, len(age_order)))), use_container_width=True)

                # Variation: Dumbbell (Q1 vs Q5) under 50
                sub50 = ec[ec["age_group"].astype(str).str.contains(r"(15-24|25-34|30-39|35-44|40-49|45-49|Y_LT50|Y_GE16_LT50)", case=False, regex=True)]
                if not sub50.empty:
                    gap = (
                        sub50.pivot_table(index="age_group", columns="income_quintile", values="exam_rate", aggfunc="median")
                        .assign(gap=lambda d: d.get("Q5") - d.get("Q1"))
                        .reset_index()
                        .dropna(subset=["gap"])
                    )
                    points = alt.Chart(gap).mark_circle(size=70).encode(
                        y=alt.Y("age_group:N", sort=age_order, title="Age group (<50)"),
                        x=alt.X("gap:Q", title="Income gap Q5 − Q1 (pp)"),
                        tooltip=["age_group", alt.Tooltip("gap:Q", format=".1f")],
                    )
                    st.altair_chart(_styled(points, title="Income gap under 50 (Q5 − Q1)", height=300), use_container_width=True)
            else:
                st.info("No rows for the chosen country/year in income survey.")
        else:
            st.info("Income × age data is missing required columns.")

    # ------------------------------------- Tab 4 -------------------------------------
    with t4:
        st.markdown("#### Correlation Lab: Does early screening reduce deaths?")
        st.markdown("**Method:** Build a country‑year panel and compute correlations across metrics.")

        # Build panel at chosen correlation year
        def _panel_for_year(y: int) -> pd.DataFrame:
            # screening (median across age groups if present)
            s = scr.copy()
            if s.empty:
                s_agg = pd.DataFrame()
            else:
                if "age" in s.columns:
                    s_agg = s[s["year"].eq(y)].groupby(["country", "year"], as_index=False)["screening_rate"].median()
                else:
                    s_agg = s[s["year"].eq(y)][["country", "year", "screening_rate"]]

            # mortality under 50 (avg of sub-bands) and total
            m = mort.copy()
            if m.empty:
                m_agg = pd.DataFrame()
            else:
                m["age"] = m.get("age", "").astype(str)
                under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
                total = m[m["age"].eq("TOTAL")]
                u = under[under["year"].eq(y)].groupby(["country", "year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate": "mort_u50"})
                t = total[total["year"].eq(y)].groupby(["country", "year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate": "mort_total"})
                m_agg = pd.merge(u, t, on=["country", "year"], how="outer")
                if not m_agg.empty:
                    m_agg["share_u50"] = (m_agg["mort_u50"] / m_agg["mort_total"]) * 100

            # income gap Q5−Q1 (<50) — use last available year <= y
            e = inc.copy()
            if e.empty:
                gap = pd.DataFrame()
            else:
                e_y = e[e["year"].le(y)]
                if e_y.empty:
                    gap = pd.DataFrame()
                else:
                    last_svy = int(e_y["year"].max())
                    sub50 = e_y[e_y["year"].eq(last_svy)]
                    sub50 = sub50[sub50["age_group"].astype(str).str.contains(r"(15-24|25-34|30-39|35-44|40-49|45-49|Y_LT50|Y_GE16_LT50)", case=False, regex=True)]
                    if sub50.empty:
                        gap = pd.DataFrame()
                    else:
                        g = (
                            sub50.pivot_table(index="country", columns="income_quintile", values="exam_rate", aggfunc="median")
                            .assign(income_gap=lambda d: d.get("Q5") - d.get("Q1"))
                            .reset_index()[["country", "income_gap"]]
                        )
                        g["svy_year"] = last_svy
                        gap = g

            panel = s_agg
            if not m_agg.empty:
                panel = pd.merge(panel, m_agg, on=["country", "year"], how="outer")
            if not gap.empty:
                panel = pd.merge(panel, gap, on="country", how="left")
            if panel is not None and not panel.empty:
                panel = panel.rename(columns={"year": "panel_year"})
            return panel

        panel = _panel_for_year(int(corr_year))
        if panel is None or panel.empty:
            st.info("Not enough overlapping data to compute correlations for this year.")
        else:
            # Scatter: screening vs mortality (under 50 preferred)
            yaxis = st.selectbox("Outcome", ["mort_u50", "share_u50", "mort_total"], index=0, help="Dependent variable for scatter plot")
            scatter = (
                alt.Chart(panel.dropna(subset=["screening_rate", yaxis]))
                .mark_circle(size=90)
                .encode(
                    x=alt.X("screening_rate:Q", title="Organized screening rate (%)"),
                    y=alt.Y(f"{yaxis}:Q", title=yaxis.replace("_", " ").title()),
                    color=alt.Color("income_gap:Q", title="Income gap (pp)", scale=alt.Scale(scheme="redpurple")),
                    tooltip=["country", "panel_year", alt.Tooltip("screening_rate:Q", format=".1f"), alt.Tooltip(f"{yaxis}:Q", format=".1f"), alt.Tooltip("income_gap:Q", format=".1f")],
                )
            )
            st.altair_chart(_styled(scatter, title=f"Correlation {corr_year}", height=360), use_container_width=True)

            # Correlation matrix of available numeric columns
            num_cols = [c for c in ["screening_rate", "mort_u50", "mort_total", "share_u50", "income_gap"] if c in panel.columns]
            if len(num_cols) >= 2:
                corr = panel[num_cols].corr().round(2).reset_index().melt("index", var_name="variable", value_name="corr")
                heat = alt.Chart(corr).mark_rect().encode(
                    x=alt.X("variable:N", title=""), y=alt.Y("index:N", title=""), color=alt.Color("corr:Q", scale=alt.Scale(scheme="redpurple"), title="r"),
                    tooltip=["index", "variable", alt.Tooltip("corr:Q", format=".2f")],
                )
                text = alt.Chart(corr).mark_text(fontWeight="bold").encode(x="variable:N", y="index:N", text=alt.Text("corr:Q", format=".2f"))
                st.altair_chart(_styled(heat + text, title="Correlation matrix"), use_container_width=True)

            # Download panel
            st.download_button("Download correlation panel (CSV)", panel.to_csv(index=False), file_name=f"correlation_panel_{corr_year}.csv")

    # ------------------------------------- Tab 5 -------------------------------------
    with t5:
        st.markdown("#### Europe Maps")
        if not _HAS_PLOTLY:
            st.warning("Plotly is not installed. Run: pip install plotly")
        else:
            # Build data for map
            metric = st.selectbox("Map metric", [
                "Screening rate (latest)",
                "Mortality under 50 (latest)",
                "Income gap Q5 − Q1 (<50, latest)",
            ], index=0)

            map_df, hover_title, color_label = None, "", ""

            if metric.startswith("Screening") and not scr.empty:
                y = int(scr["year"].dropna().max())
                d = (
                    scr[scr["year"].eq(y)].groupby("country", as_index=False)["screening_rate"].median().rename(columns={"screening_rate": "value"})
                )
                map_df = d
                hover_title = f"Screening rate ({y})"
                color_label = "Screening (%)"

            elif metric.startswith("Mortality") and not mort.empty:
                sub = mort.copy()
                sub["age"] = sub.get("age", "").astype(str)
                under = sub[sub["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
                if not under.empty:
                    y = int(under["year"].dropna().max())
                    d = under[under["year"].eq(y)].groupby("country", as_index=False)["mortality_rate"].median().rename(columns={"mortality_rate": "value"})
                    map_df = d
                    hover_title = f"Mortality under 50 ({y})"
                    color_label = "Deaths / 100k"

            else:  # Income gap
                if not inc.empty:
                    y = int(inc["year"].dropna().max())
                    e = inc[inc["year"].eq(y)]
                    sub50 = e[e["age_group"].astype(str).str.contains(r"(15-24|25-34|30-39|35-44|40-49|45-49|Y_LT50|Y_GE16_LT50)", case=False, regex=True)]
                    if not sub50.empty:
                        gap = (
                            sub50.pivot_table(index="country", columns="income_quintile", values="exam_rate", aggfunc="median")
                            .assign(value=lambda d: d.get("Q5") - d.get("Q1"))
                            .reset_index()
                            .dropna(subset=["value"])
                        )
                        map_df = gap
                        hover_title = f"Income gap (Q5 − Q1) under 50 ({y})"
                        color_label = "Gap (pp)"

            if map_df is None or map_df.empty:
                st.info("No data available for the selected metric.")
            else:
                map_df = map_df.copy()
                map_df["iso3"] = map_df["country"].map(_ISO2_TO_ISO3).fillna(map_df["country"])  # tolerate already-ISO3

                if map_kind == "Choropleth":
                    fig = px.choropleth(
                        map_df,
                        locations="iso3",
                        color="value",
                        hover_name="country",
                        color_continuous_scale="RdPu",
                        scope="europe",
                        title=hover_title,
                    )
                    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), coloraxis_colorbar=dict(title=color_label), paper_bgcolor="white", geo=dict(bgcolor="rgba(0,0,0,0)"))
                    st.plotly_chart(fig, use_container_width=True)
                else:  # Bubble map
                    # For bubble we use scatter_geo
                    fig = px.scatter_geo(
                        map_df,
                        locations="iso3",
                        hover_name="country",
                        size="value",
                        color="value",
                        color_continuous_scale="RdPu",
                        scope="europe",
                        title=hover_title + " — Bubble size encodes value",
                    )
                    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), coloraxis_colorbar=dict(title=color_label), paper_bgcolor="white", geo=dict(bgcolor="rgba(0,0,0,0)"))
                    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------- Tab 6 -------------------------------------
    with t6:
        st.markdown("#### Country Profiler")
        st.markdown("Small multiples that summarize your selection. Download the panel for custom analysis.")

        # Screening small multiples per country
        if not scr_f.empty:
            ts = scr_f.groupby(["country", "year"], as_index=False)["screening_rate"].median()
            facet = alt.Chart(ts).mark_line().encode(
                x=alt.X("year:O", title="Year"), y=alt.Y("screening_rate:Q", title="Screening (%)"),
                facet=alt.Facet("country:N", columns=3, title=None),
                tooltip=["country", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
            )
            st.altair_chart(_styled(facet, title="Screening trends — small multiples", height=120), use_container_width=True)
        else:
            st.info("No screening data for profiler.")

        # Mortality small multiples (under‑50 preferred)
        if not mort_f.empty and {"age", "mortality_rate", "year", "country"}.issubset(mort_f.columns):
            m = mort_f.copy()
            m["age"] = m["age"].astype(str)
            under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
            if under.empty:
                mt = m[m["age"].eq("TOTAL")]
            else:
                mt = under
            ts = mt.groupby(["country", "year"], as_index=False)["mortality_rate"].mean()
            facet = alt.Chart(ts).mark_line(color="#d62728").encode(
                x=alt.X("year:O", title="Year"), y=alt.Y("mortality_rate:Q", title="Deaths / 100k"),
                facet=alt.Facet("country:N", columns=3, title=None),
                tooltip=["country", "year", alt.Tooltip("mortality_rate:Q", format=".1f")],
            )
            st.altair_chart(_styled(facet, title="Mortality trends — small multiples", height=120), use_container_width=True)
        else:
            st.info("No mortality data for profiler.")

        # Download selection snapshots
        with st.expander("Download filtered tables"):
            if not scr_f.empty:
                st.download_button("Screening (filtered)", scr_f.to_csv(index=False), file_name="screening_filtered.csv")
            if not mort_f.empty:
                st.download_button("Mortality (filtered)", mort_f.to_csv(index=False), file_name="mortality_filtered.csv")
            if not inc_f.empty:
                st.download_button("Income × age (filtered)", inc_f.to_csv(index=False), file_name="exam_income_filtered.csv")
