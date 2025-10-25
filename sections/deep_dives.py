# sections/deep_dives.py
import streamlit as st
import pandas as pd
import altair as alt
import re

# Plotly just for the choropleth map
try:
    import plotly.express as px
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False


# ---------- Shared utils ----------
def _coerce_year(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df

def _year_bounds(dfs) -> tuple[int | None, int | None]:
    years = []
    for d in dfs:
        if isinstance(d, pd.DataFrame) and "year" in d.columns:
            years.extend(pd.to_numeric(d["year"], errors="coerce").dropna().unique().tolist())
    if not years:
        return None, None
    return int(min(years)), int(max(years))

def _filter_years(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    if df is None or df.empty or "year" not in df.columns:
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

def _canon_quintile(val) -> str | None:
    if pd.isna(val):
        return None
    s = str(val).strip().upper()
    m = re.match(r"^Q(U)?([1-5])$", s)
    if m: return f"Q{m.group(2)}"
    if re.fullmatch(r"[1-5]", s): return f"Q{s}"
    if re.search(r"(LOWEST|FIRST|BOTTOM)\b", s): return "Q1"
    if re.search(r"\bSECOND\b", s): return "Q2"
    if re.search(r"\bTHIRD\b", s): return "Q3"
    if re.search(r"\bFOURTH\b", s): return "Q4"
    if re.search(r"(HIGHEST|FIFTH|TOP)\b", s): return "Q5"
    return None

def _income_q1_q5_sub50(df_exam_income: pd.DataFrame) -> pd.DataFrame:
    if df_exam_income is None or df_exam_income.empty:
        return df_exam_income
    d = df_exam_income.copy()
    if "income_quintile" in d.columns:
        d["income_quintile"] = d["income_quintile"].apply(_canon_quintile)
    if "age_group" in d.columns:
        ag = d["age_group"].astype(str)
        sub50 = (
            ag.str.contains(r"Y1?5-24|Y25-34|Y30-39|Y35-44|Y40-44|Y40-49|Y45-49|Y_GE16_LT50|Y_LT50", regex=True, case=False)
            | ag.str.contains(r"\b(15-24|25-34|30-39|35-44|40-44|40-49|45-49)\b", regex=True, case=False)
        )
        d = d[sub50]
    if "income_quintile" in d.columns:
        d = d[d["income_quintile"].isin(["Q1", "Q5"])]
    return d

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

def _age_label_is_40_49_like(s: str) -> bool:
    return bool(re.search(r"\b(40-49|40-44|45-49|Y40-49|Y40-44|Y45-49)\b", s))

def _age_label_is_50_69_like(s: str) -> bool:
    return bool(re.search(r"\b(50-69|50-59|60-69|Y50-69|Y50-59|Y60-69)\b", s))

# ISO-2 → ISO-3 mapping for Europe (enough for Eurostat/your app)
_ISO2_TO_ISO3 = {
    "AT":"AUT","BE":"BEL","BG":"BGR","HR":"HRV","CY":"CYP","CZ":"CZE","DK":"DNK","EE":"EST","FI":"FIN","FR":"FRA",
    "DE":"DEU","EL":"GRC","GR":"GRC","HU":"HUN","IE":"IRL","IT":"ITA","LV":"LVA","LT":"LTU","LU":"LUX","MT":"MLT",
    "NL":"NLD","PL":"POL","PT":"PRT","RO":"ROU","SK":"SVK","SI":"SVN","ES":"ESP","SE":"SWE","IS":"ISL","NO":"NOR",
    "CH":"CHE","UK":"GBR","GB":"GBR","AL":"ALB","BA":"BIH","ME":"MNE","MK":"MKD","RS":"SRB","MD":"MDA","UA":"UKR",
    "BY":"BLR"
}
def _iso2_to_iso3(series: pd.Series) -> pd.Series:
    return series.map(_ISO2_TO_ISO3).fillna(series)


# ---------- Render ----------
def render_deep_dives(
    df_screening: pd.DataFrame | None = None,
    df_mortality: pd.DataFrame | None = None,
    df_exam_income: pd.DataFrame | None = None,
) -> None:
    """
    Deep-dive analyses with interactive charts and a Europe map.
    Tabs:
      1) Country focus
      2) Screening by age bands
      3) Under 50 burden
      4) Income vs age heatmap
      5) Interactive trends
      6) Europe map
    """

    # Local styles
    st.markdown(
        """
        <style>
        .pink-chip { display:inline-block; padding:0.18rem 0.5rem; margin:0 0.25rem 0.25rem 0;
            border-radius:999px; background:rgba(255,105,180,0.12); border:1px solid rgba(255,105,180,0.35);
            font-size:0.85rem; }
        .chip-row { margin-bottom: 0.25rem; }
        [data-testid="stMarkdownContainer"] h4 { background:#ffe6eb; padding:0.4rem 0.6rem; border-radius:6px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Deep dives")

    # Defensive coercion
    df_screening = _coerce_year(df_screening)
    df_mortality = _coerce_year(df_mortality)
    df_exam_income = _coerce_year(df_exam_income)

    # Year bounds
    y_min, y_max = _year_bounds([df_screening, df_mortality, df_exam_income])

    # Sidebar controls (shared across tabs)
    with st.sidebar:
        st.markdown("### Deep-dive filters")

        all_countries = sorted(
            pd.Index(
                list(
                    set(
                        df_screening.get("country", pd.Series(dtype=str)).dropna().unique().tolist()
                        + df_mortality.get("country", pd.Series(dtype=str)).dropna().unique().tolist()
                        + df_exam_income.get("country", pd.Series(dtype=str)).dropna().unique().tolist()
                    )
                )
            ).tolist()
        )

        country = st.selectbox("Primary country", all_countries, index=0 if all_countries else None, key="dd_primary")
        compare_countries = st.multiselect(
            "Comparison countries (optional)",
            [c for c in all_countries if c != country],
            default=[],
            key="dd_compare",
        )

        # Map metric picker (used in the Europe map tab)
        map_metric = st.selectbox(
            "Map metric",
            [
                "Screening rate (latest)",
                "Mortality rate under 50 (latest)",
                "Income gap Q5 − Q1 (<50, latest survey)",
            ],
            index=0,
            key="dd_map_metric",
        )

        if y_min is not None and y_max is not None:
            y0, y1 = st.slider("Year range", int(y_min), int(y_max), (int(y_min), int(y_max)), key="dd_years")
        else:
            y0, y1 = None, None
            st.info("No year information in the loaded tables.")

    selected_countries = [c for c in [country] + compare_countries if c]

    # Apply filters
    if y0 is not None:
        scr_f = _filter_years(_filter_countries(df_screening, selected_countries), y0, y1)
        mort_f = _filter_years(_filter_countries(df_mortality, selected_countries), y0, y1)
        exam_f = _filter_years(_filter_countries(df_exam_income, selected_countries), y0, y1)
    else:
        scr_f, mort_f, exam_f = (
            _filter_countries(df_screening, selected_countries),
            _filter_countries(df_mortality, selected_countries),
            _filter_countries(df_exam_income, selected_countries),
        )

    # Chips
    if selected_countries or y0 is not None:
        chips = " ".join([f'<span class="pink-chip">{c}</span>' for c in selected_countries]) if selected_countries else ""
        years_txt = f"{y0} to {y1}" if y0 is not None else "All years"
        st.markdown(f'<div class="chip-row">{chips}<span class="pink-chip">Years: {years_txt}</span></div>', unsafe_allow_html=True)

    # Tabs (including the new interactive & map tabs)
    t1, t2, t3, t4, t5, t6 = st.tabs(
        ["Country focus", "Screening by age bands", "Under 50 burden", "Income vs age heatmap", "Interactive trends", "Europe map"]
    )

    # ---------------- Tab 1: Country focus ----------------
    with t1:
        st.markdown("#### Country focus")

        # Screening trend
        if not scr_f.empty and {"screening_rate", "year", "country"}.issubset(scr_f.columns):
            scr_ts = (
                scr_f.groupby(["country", "year"], as_index=False)["screening_rate"].mean()
                .sort_values(["country", "year"])
            )
            color = alt.Color("country:N", legend=alt.Legend(title="Country")) if len(selected_countries) > 1 else alt.value("#1f77b4")
            line = (
                alt.Chart(scr_ts)
                .mark_line(point=True)
                .encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("screening_rate:Q", title="Organized screening rate"),
                    color=color,
                    tooltip=["country", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
                )
            )
            rule = alt.Chart(pd.DataFrame({"y": [scr_ts["screening_rate"].median()]})).mark_rule(strokeDash=[4,4]).encode(y="y:Q")
            st.altair_chart(_styled_chart(line + rule), use_container_width=True)
        else:
            st.info("Screening table not available or missing screening_rate for the selected countries.")

        # Mortality trend (under 50 where possible)
        mort_sub = _mortality_under50(mort_f)
        if mort_sub is not None and not mort_sub.empty and {"mortality_rate", "year", "country"}.issubset(mort_sub.columns):
            chart_df = mort_sub[mort_sub.get("age", "").astype(str) != "TOTAL"] if "age" in mort_sub.columns else mort_sub
            if chart_df.empty:
                chart_df = mort_sub
            mort_ts = (
                chart_df.groupby(["country", "year"], as_index=False)["mortality_rate"].mean()
                .sort_values(["country", "year"])
            )
            color = alt.Color("country:N", legend=alt.Legend(title="Country")) if len(selected_countries) > 1 else alt.value("#d62728")
            line = (
                alt.Chart(mort_ts)
                .mark_line(point=True)
                .encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("mortality_rate:Q", title="Deaths per 100000, age under 50 preferred"),
                    color=color,
                    tooltip=["country", "year", alt.Tooltip("mortality_rate:Q", format=".1f")],
                )
            )
            st.altair_chart(_styled_chart(line), use_container_width=True)
        else:
            st.info("Mortality table not available or missing mortality_rate for the selected countries.")

    # ---------------- Tab 2: Screening by age bands ----------------
    with t2:
        st.markdown("#### Screening by age bands")

        can_use_screening_age = not scr_f.empty and "age" in scr_f.columns
        if can_use_screening_age:
            s = scr_f.copy()
            s["age"] = s["age"].astype(str)
            s["band"] = None
            s.loc[s["age"].apply(_age_label_is_40_49_like), "band"] = "40–49"
            s.loc[s["age"].apply(_age_label_is_50_69_like), "band"] = "50–69"
            s = s.dropna(subset=["band"])

            if not s.empty:
                s_ts = (
                    s.groupby(["country", "year", "band"], as_index=False)["screening_rate"].mean()
                    .sort_values(["country", "band", "year"])
                )
                color = alt.Color("band:N", legend=alt.Legend(title="Age band"))
                line = (
                    alt.Chart(s_ts)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("year:O", title="Year"),
                        y=alt.Y("screening_rate:Q", title="Organized screening rate"),
                        color=color,
                        tooltip=["country", "band", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
                    )
                )
                st.altair_chart(_styled_chart(line), use_container_width=True)
            else:
                st.info("No recognizable 40–49 or 50–69 bands in df_screening for the current selection.")
        else:
            # Fallback to exam dataset comparison
            if not df_exam_income.empty and {"age_group", "exam_rate", "country", "year"}.issubset(df_exam_income.columns):
                e = _filter_countries(df_exam_income, selected_countries)
                if y0 is not None:
                    e = _filter_years(e, y0, y1)
                e["age_group"] = e["age_group"].astype(str)
                e["band"] = None
                e.loc[e["age_group"].str.contains(r"\b(40-49|40-44|45-49|Y40-49|Y40-44|Y45-49)\b", case=False, regex=True), "band"] = "40–49"
                e.loc[e["age_group"].str.contains(r"\b(50-69|50-59|60-69|Y50-69|Y50-59|Y60-69)\b", case=False, regex=True), "band"] = "50–69"
                e = e.dropna(subset=["band"])
                if not e.empty:
                    last_y = int(e["year"].dropna().max())
                    e_last = e[e["year"].eq(last_y)]
                    comp = (
                        e_last.groupby(["country", "band"], as_index=False)["exam_rate"]
                        .median()
                        .pivot(index="country", columns="band", values="exam_rate")
                        .reset_index()
                        .dropna()
                    )
                    comp["diff_50_69_minus_40_49"] = comp.get("50–69", pd.NA) - comp.get("40–49", pd.NA)
                    bars = (
                        alt.Chart(comp)
                        .mark_bar()
                        .encode(
                            x=alt.X("diff_50_69_minus_40_49:Q", title="Difference (50–69 minus 40–49), percentage points"),
                            y=alt.Y("country:N", sort="-x", title="Country"),
                            tooltip=[
                                "country",
                                alt.Tooltip("40–49:Q", format=".1f"),
                                alt.Tooltip("50–69:Q", format=".1f"),
                                alt.Tooltip("diff_50_69_minus_40_49:Q", format=".1f"),
                            ],
                        )
                    )
                    st.caption(f"Using self-reported exam rates, latest year available: {last_y}")
                    st.altair_chart(_styled_chart(bars, height=max(220, 26 * max(4, len(comp)))), use_container_width=True)
                else:
                    st.info("No recognizable 40–49 or 50–69 bands in the exam dataset for the current selection.")
            else:
                st.info("Neither screening ages nor exam ages are available for this comparison.")

    # ---------------- Tab 3: Under-50 burden ----------------
    with t3:
        st.markdown("#### Under 50 burden")
        if not mort_f.empty and {"mortality_rate", "year", "country", "age"}.issubset(mort_f.columns):
            m = mort_f.copy()
            m["age"] = m["age"].astype(str)
            under = m[m["age"].str.contains(r"(Y_LT|Y0-4|Y5-14|Y15-24|Y25-34|Y35-44|Y45-49)", regex=True, case=False)]
            total = m[m["age"].eq("TOTAL")]

            if not under.empty and not total.empty:
                under_agg = under.groupby(["country", "year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate": "mort_under50"})
                total_agg = total.groupby(["country", "year"], as_index=False)["mortality_rate"].mean().rename(columns={"mortality_rate": "mort_total"})
                merged = pd.merge(under_agg, total_agg, on=["country", "year"], how="inner")
                merged["share_under50_pct"] = (merged["mort_under50"] / merged["mort_total"]) * 100

                color = alt.Color("country:N", legend=alt.Legend(title="Country")) if len(selected_countries) > 1 else alt.value("#9467bd")
                line = (
                    alt.Chart(merged.sort_values(["country", "year"]))
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("year:O", title="Year"),
                        y=alt.Y("share_under50_pct:Q", title="Share of mortality that is under 50 (%)"),
                        color=color,
                        tooltip=[
                            "country",
                            "year",
                            alt.Tooltip("mort_under50:Q", title="Under 50 rate", format=".1f"),
                            alt.Tooltip("mort_total:Q", title="Total rate", format=".1f"),
                            alt.Tooltip("share_under50_pct:Q", title="Share under 50", format=".1f"),
                        ],
                    )
                )
                st.altair_chart(_styled_chart(line), use_container_width=True)
            else:
                st.info("Need both age-specific under-50 and TOTAL mortality to compute the share.")
        else:
            st.info("Mortality table is missing required columns to compute the under-50 share.")

    # ---------------- Tab 4: Income vs age heatmap ----------------
    with t4:
        st.markdown("#### Income vs age heatmap (latest survey year)")
        if not exam_f.empty and {"country", "year", "age_group", "income_quintile", "exam_rate"}.issubset(exam_f.columns):
            e = exam_f.copy()
            e["income_quintile"] = e["income_quintile"].apply(_canon_quintile)
            e = e.dropna(subset=["income_quintile"])

            last_year = int(e["year"].dropna().max())
            e_last = e[e["year"].eq(last_year)]

            age_order = sorted(e_last["age_group"].astype(str).unique().tolist(), key=lambda s: (len(s), s))
            quint_order = ["Q1", "Q2", "Q3", "Q4", "Q5"]

            c_heat = st.selectbox("Select country for heatmap", selected_countries or e_last["country"].unique().tolist(), key="dd_heat_country")
            e_ctry = e_last[e_last["country"].eq(c_heat)]

            if not e_ctry.empty:
                heat = (
                    alt.Chart(e_ctry)
                    .mark_rect()
                    .encode(
                        x=alt.X("income_quintile:N", sort=quint_order, title="Income quintile"),
                        y=alt.Y("age_group:N", sort=age_order, title="Age group"),
                        tooltip=[
                            "country",
                            "income_quintile",
                            "age_group",
                            alt.Tooltip("exam_rate:Q", format=".1f", title="Exam rate"),
                        ],
                        color=alt.Color("exam_rate:Q", title="Exam rate", scale=alt.Scale(scheme="reds")),
                    )
                )
                st.caption(f"Latest survey year available: {last_year}")
                st.altair_chart(_styled_chart(heat, height=max(260, 18 * max(8, len(age_order)))) , use_container_width=True)
            else:
                st.info("No rows for the chosen country in the latest survey year.")
        else:
            st.info("Exam by income data is missing required columns for the heatmap.")

    # ---------------- Tab 5: Interactive trends (Altair) ----------------
    with t5:
        st.markdown("#### Interactive screening trend (hover, click highlight, brush zoom)")

        if not scr_f.empty and {"screening_rate", "year", "country"}.issubset(scr_f.columns):
            ts = scr_f.groupby(["country", "year"], as_index=False)["screening_rate"].mean().sort_values(["country", "year"])

            hover = alt.selection_point(fields=["year"], nearest=True, on="pointerover", empty=False, clear="pointerout")
            select_country = alt.selection_point(fields=["country"], on="click", bind="legend")
            brush = alt.selection_interval(encodings=["x"])

            base = alt.Chart(ts).encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y("screening_rate:Q", title="Organized screening rate"),
                color=alt.condition(select_country, alt.Color("country:N", title="Country"), alt.value("#d3d3d3")),
                tooltip=["country", "year", alt.Tooltip("screening_rate:Q", format=".1f")],
            )
            lines = base.mark_line().add_params(select_country)
            points = base.mark_point(filled=True, size=40).add_params(hover).transform_filter(select_country | (select_country.isempty()))
            rules = alt.Chart(ts).mark_rule(color="lightgray").encode(x="year:O").transform_filter(hover)
            text = base.mark_text(align="left", dx=5, dy=-5).encode(text=alt.condition(hover, alt.datum.screening_rate, alt.value("")))

            zoomed = (lines + points + rules + text).add_params(brush).transform_filter(brush)
            st.altair_chart(_styled_chart(zoomed).interactive(), use_container_width=True)
        else:
            st.info("Screening table not available or missing screening_rate.")

        st.markdown("#### Latest screening level by country")
        if not scr_f.empty and {"screening_rate", "year", "country"}.issubset(scr_f.columns):
            latest_y = int(scr_f["year"].dropna().max())
            latest = (
                scr_f[scr_f["year"].eq(latest_y)]
                .groupby("country", as_index=False)["screening_rate"]
                .median()
                .sort_values("screening_rate", ascending=False)
            )

            hover_bar = alt.selection_point(fields=["country"], on="pointerover", empty="all", clear="pointerout")
            bars = (
                alt.Chart(latest)
                .mark_bar()
                .encode(
                    y=alt.Y("country:N", sort="-x"),
                    x=alt.X("screening_rate:Q", title=f"Screening rate in {latest_y}"),
                    color=alt.condition(hover_bar, alt.value("#1f77b4"), alt.value("#aac6e7")),
                    tooltip=["country", alt.Tooltip("screening_rate:Q", format=".1f")],
                )
                .add_params(hover_bar)
            )
            st.altair_chart(_styled_chart(bars, height=max(220, 24 * max(4, len(latest)))), use_container_width=True)
        else:
            st.info("Not enough screening data for cross-section view.")

    # ---------------- Tab 6: Europe map (Plotly choropleth) ----------------
    with t6:
        st.markdown("#### Europe map")
        if not _HAS_PLOTLY:
            st.warning("Plotly is not installed. Run: pip install plotly")
            return

        map_df = None
        hover_title = ""
        color_label = ""

        if map_metric.startswith("Screening"):
            if not df_screening.empty and {"screening_rate", "year", "country"}.issubset(df_screening.columns):
                # use the overall filtered country set, but last year across *all* (richer map)
                scr_all = _filter_years(df_screening, y0, y1) if y0 is not None else df_screening
                y = int(scr_all["year"].dropna().max())
                d = (
                    scr_all[scr_all["year"].eq(y)]
                    .groupby("country", as_index=False)["screening_rate"]
                    .median()
                    .rename(columns={"screening_rate":"value"})
                )
                d["iso3"] = _iso2_to_iso3(d["country"])
                map_df = d
                hover_title = f"Organized screening rate ({y})"
                color_label = "Screening rate"
        elif map_metric.startswith("Mortality"):
            mort_all = _filter_years(df_mortality, y0, y1) if y0 is not None else df_mortality
            mort_sub_all = _mortality_under50(mort_all)
            if mort_sub_all is not None and not mort_sub_all.empty and {"mortality_rate","year","country"}.issubset(mort_sub_all.columns):
                m = mort_sub_all[mort_sub_all.get("age","").astype(str)!="TOTAL"] if "age" in mort_sub_all.columns else mort_sub_all
                if m.empty: m = mort_sub_all
                y = int(m["year"].dropna().max())
                d = (
                    m[m["year"].eq(y)]
                    .groupby("country", as_index=False)["mortality_rate"]
                    .median()
                    .rename(columns={"mortality_rate":"value"})
                )
                d["iso3"] = _iso2_to_iso3(d["country"])
                map_df = d
                hover_title = f"Mortality rate (under 50 preferred) ({y})"
                color_label = "Deaths per 100k"
        else:
            # Income gap Q5 − Q1
            exam_all = _filter_years(df_exam_income, y0, y1) if y0 is not None else df_exam_income
            ei_sub_all = _income_q1_q5_sub50(exam_all)
            if ei_sub_all is not None and not ei_sub_all.empty and {"income_quintile","exam_rate","year","country"}.issubset(ei_sub_all.columns):
                y = int(ei_sub_all["year"].dropna().max())
                e = ei_sub_all[ei_sub_all["year"].eq(y)]
                gap = (
                    e.pivot_table(index="country", columns="income_quintile", values="exam_rate", aggfunc="median")
                    .assign(value=lambda d: d.get("Q5") - d.get("Q1"))
                    .reset_index()
                    .dropna(subset=["value"])
                )
                gap["iso3"] = _iso2_to_iso3(gap["country"])
                map_df = gap
                hover_title = f"Income gap (Q5 − Q1) in exam rate, under 50 ({y})"
                color_label = "Gap (pp)"

        if map_df is None or map_df.empty or "iso3" not in map_df.columns:
            st.info("No data available for the selected map metric and filters.")
            return

        fig = px.choropleth(
            map_df,
            locations="iso3",
            color="value",
            hover_name="country",
            color_continuous_scale="RdPu",
            scope="europe",
            title=hover_title,
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_colorbar=dict(title=color_label),
        )
        st.plotly_chart(fig, use_container_width=True)
