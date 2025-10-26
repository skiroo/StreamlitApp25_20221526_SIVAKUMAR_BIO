# sections/deep_dives.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import altair as alt
import re

try:
    import plotly.express as px
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False

# -------- Normalizers --------
def _normalize_screening(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.rename(columns={"geo":"country","TIME_PERIOD":"year","OBS_VALUE":"screening_rate"}).copy()
    if "icd10" in d.columns: d = d[d["icd10"].astype(str).str.upper().eq("C50")]
    if "source" in d.columns: d = d[d["source"].astype(str).str.upper().eq("PRG")]
    if "year" in d.columns: d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    if "screening_rate" in d.columns: d["screening_rate"] = pd.to_numeric(d["screening_rate"], errors="coerce")
    return d

def _normalize_mortality(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.rename(columns={"geo":"country","TIME_PERIOD":"year","OBS_VALUE":"mortality_rate"}).copy()
    if "sex" in d.columns: d = d[d["sex"].astype(str).str.upper().str.contains("F", na=False)]
    if "icd10" in d.columns: d = d[d["icd10"].astype(str).str.upper().str.contains("C50", na=False)]
    if "year" in d.columns: d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    if "mortality_rate" in d.columns: d["mortality_rate"] = pd.to_numeric(d["mortality_rate"], errors="coerce")
    return d

def _normalize_income(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.rename(columns={"geo":"country","TIME_PERIOD":"year","OBS_VALUE":"exam_rate",
                           "quant_inc":"income_quintile","age":"age_group"}).copy()
    def _canon_quintile(v):
        if pd.isna(v): return None
        s = str(v).upper().strip()
        m = re.match(r"^Q(U)?([1-5])$", s)
        if m: return f"Q{m.group(2)}"
        if re.fullmatch(r"[1-5]", s): return f"Q{s}"
        if "LOW" in s or "FIRST" in s or "BOTTOM" in s: return "Q1"
        if "SECOND" in s: return "Q2"
        if "THIRD" in s: return "Q3"
        if "FOURTH" in s: return "Q4"
        if "HIGH" in s or "FIFTH" in s or "TOP" in s: return "Q5"
        return None
    if "income_quintile" in d.columns: d["income_quintile"] = d["income_quintile"].apply(_canon_quintile)
    if "year" in d.columns: d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    if "exam_rate" in d.columns: d["exam_rate"] = pd.to_numeric(d["exam_rate"], errors="coerce")
    return d

# ISO-2 → ISO-3 for maps
_ISO2_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","HR":"HRV","CY":"CYP","CZ":"CZE","DK":"DNK","EE":"EST","FI":"FIN","FR":"FRA",
    "DE":"DEU","EL":"GRC","GR":"GRC","HU":"HUN","IE":"IRL","IT":"ITA","LV":"LVA","LT":"LTU","LU":"LUX","MT":"MLT",
    "NL":"NLD","PL":"POL","PT":"PRT","RO":"ROU","SK":"SVK","SI":"SVN","ES":"ESP","SE":"SWE","IS":"ISL","NO":"NOR",
    "CH":"CHE","UK":"GBR","GB":"GBR","AL":"ALB","BA":"BIH","ME":"MNE","MK":"MKD","RS":"SRB","MD":"MDA","UA":"UKR","BY":"BLR"
}

def _styled(chart: alt.Chart, title: str = "", height: int | None = None):
    base = chart.properties(title=title, width="container")
    if height:
        base = base.properties(height=height)
    return (base
            .configure_view(stroke="#e6e6e6", strokeWidth=1)
            .configure_title(anchor="start", fontSize=14, color="#1e1e1e", fontWeight="bold")
            .configure_axis(grid=False, domainColor="#f3a1c0", labelColor="#333", titleColor="#333")
            .configure_legend(titleColor="#333", labelColor="#333"))

def render_deep_dives(df_screening: pd.DataFrame | None = None,
                      df_mortality: pd.DataFrame | None = None,
                      df_exam_income: pd.DataFrame | None = None) -> None:
    st.subheader("Deep Dives")
    st.caption("Global filters live in the sidebar. Each tab adds its own lightweight controls.")

    scr = _normalize_screening(df_screening)
    mort = _normalize_mortality(df_mortality)
    inc  = _normalize_income(df_exam_income)

    # ---- read global filters ----
    gf = st.session_state.get("global_filters", {}) or {}
    sel_countries = gf.get("countries", ["FR"]) or ["FR"]
    y0, y1 = gf.get("y0"), gf.get("y1")

    def _sub(df):
        if df is None or df.empty: return df
        d = df.copy()
        if "year" in d.columns and y0 is not None and y1 is not None:
            d = d[(d["year"] >= y0) & (d["year"] <= y1)]
        if "country" in d.columns and sel_countries:
            d = d[d["country"].isin(sel_countries)]
        return d

    scr_f, mort_f, inc_f = _sub(scr), _sub(mort), _sub(inc)

    t1, t2, t3, t4, t5 = st.tabs([
        "Screening: Early vs Recommended",
        "Burden shift: Under-50",
        "Inequality: Income × Age",
        "Correlation Lab",
        "Europe Maps",
    ])

    # ===== Tab 1: Screening bands =====
    with t1:
        st.markdown("#### Are we screening enough — and early enough?")
        if not scr_f.empty:
            s = scr_f.copy()
            if "age" in s.columns:
                s["age"] = s["age"].astype(str)
                band4049 = s["age"].str.contains(r"\b(40-49|40-44|45-49|Y40-49|Y40-44|Y45-49)\b", regex=True, case=False)
                band5069 = s["age"].str.contains(r"\b(50-69|50-59|60-69|Y50-69|Y50-59|Y60-69)\b", regex=True, case=False)
                s["band"] = None
                s.loc[band4049, "band"] = "40–49"
                s.loc[band5069, "band"] = "50–69"
                s = s.dropna(subset=["band"])
                if not s.empty:
                    ts = s.groupby(["country","year","band"], as_index=False)["screening_rate"].median().sort_values(["country","band","year"])
                    color = alt.Color("band:N", title="Age band")
                    line = alt.Chart(ts).mark_line(point=True).encode(
                        x=alt.X("year:O", title="Year"),
                        y=alt.Y("screening_rate:Q", title="Organized screening rate (%)"),
                        color=color,
                        tooltip=["country","band","year",alt.Tooltip("screening_rate:Q", format=".1f")]
                    )
                    st.altair_chart(_styled(line, height=360), use_container_width=True)
                else:
                    st.info("Age-specific screening bands not available in this selection.")
            else:
                ts = scr_f.groupby(["country","year"], as_index=False)["screening_rate"].median().sort_values(["country","year"])
                line = alt.Chart(ts).mark_line(point=True).encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("screening_rate:Q", title="Organized screening rate (%)"),
                    color=alt.Color("country:N", title="Country"),
                    tooltip=["country","year",alt.Tooltip("screening_rate:Q", format=".1f")]
                )
                st.altair_chart(_styled(line, height=360), use_container_width=True)
        else:
            st.info("No screening data for current filters.")

    # ===== Tab 2: Burden shift =====
    with t2:
        st.markdown("#### Is the burden shifting to younger women?")
        if not mort_f.empty and {"mortality_rate","age","year","country"}.issubset(mort_f.columns):
            m = mort_f.copy()
            m["age"] = m["age"].astype(str)
            under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
            total = m[m["age"].eq("TOTAL")]
            if not under.empty and not total.empty:
                u = under.groupby(["country","year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate":"mort_u50"})
                t = total.groupby(["country","year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate":"mort_total"})
                g = pd.merge(u, t, on=["country","year"], how="inner")
                g["share_u50"] = (g["mort_u50"] / g["mort_total"]) * 100
                sel = alt.selection_point(fields=["country"], bind="legend")
                chart = alt.Chart(g).mark_line(point=True).encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("share_u50:Q", title="Share under 50 (%)"),
                    color=alt.condition(sel, alt.Color("country:N", title="Country"), alt.value("#d3d3d3")),
                    tooltip=["country","year",alt.Tooltip("share_u50:Q", format=".1f")]
                ).add_params(sel)
                st.altair_chart(_styled(chart, height=360), use_container_width=True)
            else:
                st.info("Need both under-50 and TOTAL mortality to compute the share.")
        else:
            st.info("Mortality data incomplete for this analysis.")

    # ===== Tab 3: Inequality =====
    with t3:
        st.markdown("#### Who gets screened — and who doesn’t?")
        if not inc_f.empty and {"country","year","age_group","income_quintile","exam_rate"}.issubset(inc_f.columns):
            last_y = int(inc_f["year"].dropna().max())
            e = inc_f[inc_f["year"].eq(last_y)].copy()
            st.caption(f"Latest survey year available: {last_y}")
            default_country = (sel_countries[0] if sel_countries else e["country"].iloc[0])
            c_heat = st.selectbox("Choose country", sorted(e["country"].unique().tolist()),
                                  index=sorted(e["country"].unique()).index(default_country))
            ec = e[e["country"].eq(c_heat)]
            if not ec.empty:
                age_order = sorted(ec["age_group"].astype(str).unique().tolist(), key=lambda s: (len(s), s))
                heat = alt.Chart(ec).mark_rect().encode(
                    x=alt.X("income_quintile:N", sort=["Q1","Q2","Q3","Q4","Q5"], title="Income quintile"),
                    y=alt.Y("age_group:N", sort=age_order, title="Age group"),
                    color=alt.Color("exam_rate:Q", title="Exam rate (%)", scale=alt.Scale(scheme="reds")),
                    tooltip=["country","income_quintile","age_group",alt.Tooltip("exam_rate:Q", format=".1f")]
                )
                st.altair_chart(_styled(heat, height=max(260, 18 * max(8, len(age_order)))), use_container_width=True)
        else:
            st.info("Income × age table is missing required columns.")

    # ===== Tab 4: Correlation Lab =====
    with t4:
        st.markdown("#### Correlation Lab")
        # pick a correlation year inside the tab (default = latest overall)
        y_candidates = scr["year"].dropna().tolist() + mort["year"].dropna().tolist()
        if not y_candidates:
            st.info("No year available for correlation.")
        else:
            corr_year = st.slider("Correlation year", int(min(y_candidates)), int(max(y_candidates)), int(max(y_candidates)))
            def _panel_for_year(y: int) -> pd.DataFrame:
                # screening
                if scr.empty: s_agg = pd.DataFrame()
                else:
                    if "age" in scr.columns:
                        s_agg = scr[scr["year"].eq(y)].groupby(["country","year"], as_index=False)["screening_rate"].median()
                    else:
                        s_agg = scr[scr["year"].eq(y)][["country","year","screening_rate"]]
                # mortality
                if mort.empty: m_agg = pd.DataFrame()
                else:
                    m = mort.copy(); m["age"] = m.get("age","").astype(str)
                    under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
                    total = m[m["age"].eq("TOTAL")]
                    u = under[under["year"].eq(y)].groupby(["country","year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate":"mort_u50"})
                    t = total[total["year"].eq(y)].groupby(["country","year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate":"mort_total"})
                    m_agg = pd.merge(u,t,on=["country","year"], how="outer")
                    if not m_agg.empty:
                        m_agg["share_u50"] = (m_agg["mort_u50"] / m_agg["mort_total"]) * 100
                # income gap (last <= y)
                if inc.empty: g = pd.DataFrame()
                else:
                    e_y = inc[inc["year"].le(y)]
                    if e_y.empty: g = pd.DataFrame()
                    else:
                        last_svy = int(e_y["year"].max())
                        sub = e_y[e_y["year"].eq(last_svy)]
                        sub = sub[sub["age_group"].astype(str).str.contains(r"(15-24|25-34|30-39|35-44|40-49|45-49|Y_LT50|Y_GE16_LT50)", regex=True, case=False)]
                        if sub.empty: g = pd.DataFrame()
                        else:
                            g = (sub.pivot_table(index="country", columns="income_quintile", values="exam_rate", aggfunc="median")
                                     .assign(income_gap=lambda d: d.get("Q5") - d.get("Q1"))
                                     .reset_index()[["country","income_gap"]])
                            g["svy_year"] = last_svy
                panel = s_agg
                if not m_agg.empty: panel = pd.merge(panel, m_agg, on=["country","year"], how="outer")
                if not g.empty: panel = pd.merge(panel, g, on="country", how="left")
                if panel is not None and not panel.empty: panel = panel.rename(columns={"year":"panel_year"})
                return panel
            panel = _panel_for_year(int(corr_year))
            if panel is None or panel.empty:
                st.info("Not enough overlapping data to compute correlations.")
            else:
                yaxis = st.selectbox("Outcome", ["mort_u50","share_u50","mort_total"], index=0)
                pretty = {"mort_u50":"Mortality under 50 (per 100k)","share_u50":"Share under 50 (%)","mort_total":"Mortality total (per 100k)"}[yaxis]
                scatter = alt.Chart(panel.dropna(subset=["screening_rate", yaxis])).mark_circle(size=90).encode(
                    x=alt.X("screening_rate:Q", title="Organized screening rate (%)"),
                    y=alt.Y(f"{yaxis}:Q", title=pretty),
                    color=alt.Color("income_gap:Q", title="Income gap (pp)", scale=alt.Scale(scheme="redpurple")),
                    tooltip=["country","panel_year",alt.Tooltip("screening_rate:Q", format=".1f"),alt.Tooltip(f"{yaxis}:Q", format=".1f"),alt.Tooltip("income_gap:Q", format=".1f")]
                )
                st.altair_chart(_styled(scatter, title=f"Correlation {corr_year}", height=360), use_container_width=True)

                # Matrix
                num_cols = [c for c in ["screening_rate","mort_u50","mort_total","share_u50","income_gap"] if c in panel.columns]
                if len(num_cols) >= 2:
                    corr = panel[num_cols].corr().round(2).reset_index().melt("index", var_name="variable", value_name="corr")
                    heat = alt.Chart(corr).mark_rect().encode(
                        x=alt.X("variable:N", title=""), y=alt.Y("index:N", title=""),
                        color=alt.Color("corr:Q", scale=alt.Scale(scheme="redpurple"), title="r"),
                        tooltip=["index","variable",alt.Tooltip("corr:Q", format=".2f")]
                    )
                    text = alt.Chart(corr).mark_text(fontWeight="bold").encode(x="variable:N", y="index:N", text=alt.Text("corr:Q", format=".2f"))
                    st.altair_chart(_styled(heat + text, title="Correlation matrix"), use_container_width=True)

    # ===== Tab 5: Europe Maps with animated year slider =====
    with t5:
        st.markdown("#### Europe Maps")
        if not _HAS_PLOTLY:
            st.warning("Plotly is required for map animation. pip install plotly")
        else:
            # Build long panel for animation
            frames = []
            if not scr.empty:
                g = scr.groupby(["country","year"], as_index=False)["screening_rate"].median()
                g["metric"] = "Screening (%)"; g = g.rename(columns={"screening_rate":"value"}); frames.append(g)
            if not mort.empty and "age" in mort.columns:
                m = mort.copy(); m["age"] = m["age"].astype(str)
                under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
                if not under.empty:
                    g = under.groupby(["country","year"], as_index=False)["mortality_rate"].mean()
                    g["metric"] = "Mortality under 50 (per 100k)"; g = g.rename(columns={"mortality_rate":"value"}); frames.append(g)
            if not inc.empty:
                e = inc.copy()
                ag = e["age_group"].astype(str)
                sub50 = e[ag.str.contains(r"(15-24|25-34|30-39|35-44|40-49|45-49|Y_LT50|Y_GE16_LT50)", regex=True, case=False)]
                if not sub50.empty:
                    gap = (sub50.pivot_table(index=["country","year"], columns="income_quintile", values="exam_rate", aggfunc="median")
                                .assign(value=lambda d: d.get("Q5") - d.get("Q1"))
                                .reset_index()
                                .dropna(subset=["value"]))
                    gap["metric"] = "Income gap Q5−Q1 (<50, pp)"; frames.append(gap[["country","year","value","metric"]])
            if not frames:
                st.info("No data available for maps.")
            else:
                panel = pd.concat(frames, ignore_index=True)
                if y0 is not None and y1 is not None:
                    panel = panel[(panel["year"] >= y0) & (panel["year"] <= y1)]
                panel["iso3"] = panel["country"].map(_ISO2_TO_ISO3).fillna(panel["country"])
                metric = st.selectbox("Metric", ["Screening (%)","Mortality under 50 (per 100k)","Income gap Q5−Q1 (<50, pp)"], index=0)
                map_kind = st.radio("Map type", ["Choropleth", "Bubble"], index=0, horizontal=True)
                data = panel[panel["metric"].eq(metric)].sort_values("year")
                if data.empty:
                    st.info("Metric not available for current selection.")
                else:
                    if map_kind == "Choropleth":
                        fig = px.choropleth(
                            data, locations="iso3", color="value", scope="europe",
                            color_continuous_scale="RdPu", animation_frame="year",
                            title=metric
                        )
                    else:
                        fig = px.scatter_geo(
                            data, locations="iso3", size="value", color="value",
                            color_continuous_scale="RdPu", scope="europe",
                            animation_frame="year", title=metric + " — Bubble size encodes value"
                        )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=40, b=0),
                        coloraxis_colorbar=dict(title=metric.split("(")[0].strip()),
                        paper_bgcolor="white",
                        geo=dict(bgcolor="rgba(0,0,0,0)")
                    )
                    st.plotly_chart(fig, use_container_width=True)
