# sections/conclusion.py
import streamlit as st
import pandas as pd
import altair as alt
from typing import Iterable


# ---------------- Utilities (kept local so this file is standalone) ----------------
def _coerce_year(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    d = df.copy()
    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce")
    return d

def _year_bounds(dfs: Iterable[pd.DataFrame]) -> tuple[int | None, int | None]:
    years = []
    for d in dfs:
        if isinstance(d, pd.DataFrame) and "year" in d.columns:
            years.extend(pd.to_numeric(d["year"], errors="coerce").dropna().unique().tolist())
    if not years:
        return None, None
    return int(min(years)), int(max(years))

def _filter_years(df: pd.DataFrame, y0: int | None, y1: int | None) -> pd.DataFrame:
    if df is None or df.empty or "year" not in df.columns or y0 is None or y1 is None:
        return df
    return df[(df["year"] >= y0) & (df["year"] <= y1)]

def _filter_countries(df: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    if df is None or df.empty or "country" not in df.columns or not countries:
        return df
    return df[df["country"].isin(countries)]

def _mortality_under50(df_mortality: pd.DataFrame) -> pd.DataFrame:
    """
    Keep under-50 ages if present; keep TOTAL as fallback so that
    the page always renders something even with coarse age coding.
    """
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

def _styled_chart(chart, title=None, height=220):
    """Uniform border + clean axes."""
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
        .configure_title(anchor="start", fontSize=13, color="#222", fontWeight="bold")
    )

def _trend_wording(first_val: float | None, last_val: float | None, up_word="has increased", down_word="has decreased") -> str | None:
    """
    Return a short phrase describing trend direction based on first vs last.
    Uses a small threshold to avoid calling noise a trend.
    """
    if first_val is None or pd.isna(first_val) or last_val is None or pd.isna(last_val):
        return None
    diff = float(last_val) - float(first_val)
    # threshold in natural units: 1.0 for percentages or per-100k rates
    if diff >= 1.0:
        return f"{up_word} by {diff:.1f}"
    if diff <= -1.0:
        return f"{down_word} by {abs(diff):.1f}"
    return "has remained relatively stable"


# ---------------- Render ----------------
def render_conclusion(
    df_screening: pd.DataFrame | None = None,
    df_mortality: pd.DataFrame | None = None,
    df_exam_income: pd.DataFrame | None = None,
) -> None:
    """
    Final conclusions, KPIs, mini-trends, caveats, and downloads.

    Expected columns from the pipeline (robust to partial availability):
      df_screening:  country, year, screening_rate [, age?]
      df_mortality:  country, year, age, sex, icd10, mortality_rate
      df_exam_income: country, year, duration, age_group, income_quintile, exam_rate
    """

    # Local style
    st.markdown(
        """
        <style>
        .pink-chip {
            display:inline-block; padding:0.18rem 0.5rem; margin:0 0.25rem 0.25rem 0;
            border-radius:999px; background:rgba(255,105,180,0.12);
            border:1px solid rgba(255,105,180,0.35); font-size:0.85rem;
        }
        .chip-row { margin: 0.25rem 0 0.5rem 0; }
        .note-box {
            border:1px solid #f2a7bc; background:#fff5f8; padding:0.75rem; border-radius:8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Conclusion & next steps")

    # Defensive copies / coercions
    df_screening = _coerce_year(df_screening)
    df_mortality = _coerce_year(df_mortality)
    df_exam_income = _coerce_year(df_exam_income)

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Conclusion filters")

        # Countries universe
        all_countries = sorted(
            pd.Index(
                list(
                    set(
                        (df_screening["country"].dropna().unique().tolist() if "country" in df_screening.columns else [])
                        + (df_mortality["country"].dropna().unique().tolist() if "country" in df_mortality.columns else [])
                        + (df_exam_income["country"].dropna().unique().tolist() if "country" in df_exam_income.columns else [])
                    )
                )
            ).tolist()
        )
        default_sel = all_countries[:6]

        countries = st.multiselect(
            "Countries",
            options=all_countries,
            default=default_sel,
            key="concl_countries",
        )

        y_min, y_max = _year_bounds([df_screening, df_mortality, df_exam_income])
        if y_min is not None and y_max is not None:
            y0, y1 = st.slider("Year range", int(y_min), int(y_max), (int(y_min), int(y_max)), key="concl_years")
        else:
            y0, y1 = None, None
            st.info("No year information in the loaded tables.")

    # Apply filters
    scr_f = _filter_countries(df_screening, countries)
    mort_f = _filter_countries(df_mortality, countries)
    exam_f = _filter_countries(df_exam_income, countries)

    scr_f = _filter_years(scr_f, y0, y1)
    mort_f = _filter_years(mort_f, y0, y1)
    exam_f = _filter_years(exam_f, y0, y1)

    # Chips
    if countries or (y0 is not None and y1 is not None):
        chips = " ".join([f'<span class="pink-chip">{c}</span>' for c in countries]) if countries else ""
        years_txt = f"{int(y0)} to {int(y1)}" if (y0 is not None and y1 is not None) else "All years"
        st.markdown(f'<div class="chip-row">{chips}<span class="pink-chip">Years: {years_txt}</span></div>', unsafe_allow_html=True)

    # ---------------- KPIs (from filtered slice) ----------------
    k1, k2, k3 = st.columns(3)

    # KPI 1: Screening median latest and delta vs first
    scr_val, scr_delta = "—", ""
    scr_first, scr_last = None, None
    if not scr_f.empty and {"screening_rate", "year"}.issubset(scr_f.columns):
        ys = scr_f["year"].dropna()
        if not ys.empty:
            y_last, y_first = int(ys.max()), int(ys.min())
            latest = scr_f[scr_f["year"].eq(y_last)]["screening_rate"].median()
            base = scr_f[scr_f["year"].eq(y_first)]["screening_rate"].median()
            scr_first, scr_last = base, latest
            if pd.notna(latest):
                scr_val = f"{latest:.1f}"
            if pd.notna(latest) and pd.notna(base):
                scr_delta = f"{(latest - base):+,.1f} vs {y_first}"
    k1.metric("Organized screening median (latest)", scr_val, scr_delta)

    # KPI 2: Mortality under 50 median latest and delta vs first (fallback to TOTAL if needed)
    mort_val, mort_delta = "—", ""
    mort_first, mort_last = None, None
    mort_sub = _mortality_under50(mort_f)
    if mort_sub is not None and not mort_sub.empty and {"mortality_rate", "year"}.issubset(mort_sub.columns):
        # prefer explicit under-50 rows; else use what's available
        explicit = mort_sub[mort_sub.get("age", "").astype(str) != "TOTAL"] if "age" in mort_sub.columns else mort_sub
        muse = explicit if not explicit.empty else mort_sub
        ys = muse["year"].dropna()
        if not ys.empty:
            y_last, y_first = int(ys.max()), int(ys.min())
            latest = muse[muse["year"].eq(y_last)]["mortality_rate"].median()
            base = muse[muse["year"].eq(y_first)]["mortality_rate"].median()
            mort_first, mort_last = base, latest
            if pd.notna(latest):
                mort_val = f"{latest:.1f}"
            if pd.notna(latest) and pd.notna(base):
                mort_delta = f"{(latest - base):+,.1f} vs {y_first}"
    k2.metric("Mortality median (under 50 preferred, latest)", mort_val, mort_delta)

    # KPI 3: Income gap Q5 − Q1 (under 50, latest survey year)
    gap_val, gap_note = "—", ""
    gap_year = None
    if not exam_f.empty and {"income_quintile", "exam_rate", "year"}.issubset(exam_f.columns):
        # Canonicalize quintiles quickly if needed
        qcol = exam_f["income_quintile"].astype(str).str.upper()
        ei = exam_f.copy()
        ei.loc[qcol.str.match(r"^QU([1-5])$"), "income_quintile"] = "Q" + qcol.str.extract(r"^QU([1-5])$")[0]
        ys = ei["year"].dropna()
        if not ys.empty:
            y_last = int(ys.max())
            e_last = ei[ei["year"].eq(y_last)]
            q5 = e_last[e_last["income_quintile"].eq("Q5")]["exam_rate"].median()
            q1 = e_last[e_last["income_quintile"].eq("Q1")]["exam_rate"].median()
            if pd.notna(q5) and pd.notna(q1):
                gap_val = f"{(q5 - q1):.1f} pp"
                gap_note = f"Year {y_last}"
                gap_year = y_last
    k3.metric("Income gap in last X-ray exam (<50): Q5 − Q1", gap_val, gap_note)

    st.markdown("---")

    # ---------------- Mini-trends (medians across selected countries) ----------------
    c1, c2 = st.columns(2)

    scr_med, mort_med = pd.DataFrame(), pd.DataFrame()
    with c1:
        st.markdown("#### Median screening over time")
        if not scr_f.empty and {"screening_rate", "year"}.issubset(scr_f.columns):
            scr_med = (
                scr_f.groupby("year", as_index=False)["screening_rate"]
                .median()
                .dropna(subset=["year", "screening_rate"])
                .sort_values("year")
            )
            if not scr_med.empty:
                line = (
                    alt.Chart(scr_med)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("year:Q", title="Year"),
                        y=alt.Y("screening_rate:Q", title="Median screening rate"),
                        tooltip=[alt.Tooltip("year:Q", format=".0f"), alt.Tooltip("screening_rate:Q", format=".1f")],
                    )
                )
                st.altair_chart(_styled_chart(line), use_container_width=True)
            else:
                st.info("No screening rows in the selected range.")
        else:
            st.info("Screening table not available or missing columns.")

    with c2:
        st.markdown("#### Median mortality (under 50 preferred)")
        m_sub = _mortality_under50(mort_f)
        if m_sub is not None and not m_sub.empty and {"mortality_rate", "year"}.issubset(m_sub.columns):
            # prefer explicit under-50
            explicit = m_sub[m_sub.get("age", "").astype(str) != "TOTAL"] if "age" in m_sub.columns else m_sub
            muse = explicit if not explicit.empty else m_sub
            mort_med = (
                muse.groupby("year", as_index=False)["mortality_rate"]
                .median()
                .dropna(subset=["year", "mortality_rate"])
                .sort_values("year")
            )
            if not mort_med.empty:
                line = (
                    alt.Chart(mort_med)
                    .mark_line(point=True, color="#d62728")
                    .encode(
                        x=alt.X("year:Q", title="Year"),
                        y=alt.Y("mortality_rate:Q", title="Median deaths per 100,000"),
                        tooltip=[alt.Tooltip("year:Q", format=".0f"), alt.Tooltip("mortality_rate:Q", format=".1f")],
                    )
                )
                st.altair_chart(_styled_chart(line), use_container_width=True)
            else:
                st.info("No mortality rows in the selected range.")
        else:
            st.info("Mortality table not available or missing columns.")

    # ---------------- Sentence-style takeaways ----------------
    st.markdown("### What the data suggests")
    paragraphs = []

    # Screening sentence
    if scr_last is not None:
        # Trend wording from medians if available; otherwise from first/last KPIs
        scr_trend_phrase = None
        if not scr_med.empty:
            first_y, last_y = scr_med["year"].iloc[0], scr_med["year"].iloc[-1]
            scr_trend_phrase = _trend_wording(
                float(scr_med["screening_rate"].iloc[0]),
                float(scr_med["screening_rate"].iloc[-1]),
                up_word="has increased",
                down_word="has decreased",
            )
        else:
            scr_trend_phrase = _trend_wording(scr_first, scr_last, up_word="has increased", down_word="has decreased")

        sentence = f"In the selected countries and years, the median **organized screening rate** is **{scr_last:.1f}%** in the latest year. "
        if scr_trend_phrase:
            sentence += f"Across the period, it {scr_trend_phrase}."
        if isinstance(scr_delta, str) and scr_delta:
            sentence += f" That corresponds to a change of {scr_delta.replace(' vs', ' since')}."
        paragraphs.append(sentence)

    # Mortality sentence
    if mort_last is not None:
        mort_trend_phrase = None
        if not mort_med.empty:
            mort_trend_phrase = _trend_wording(
                float(mort_med["mortality_rate"].iloc[0]) if not mort_med.empty else None,
                float(mort_med["mortality_rate"].iloc[-1]) if not mort_med.empty else None,
                up_word="has increased",
                down_word="has decreased",
            )
        else:
            mort_trend_phrase = _trend_wording(mort_first, mort_last, up_word="has increased", down_word="has decreased")

        sentence = (
            f"For **mortality** (under 50 preferred when available), the median rate is **{mort_last:.1f} per 100,000** "
            f"in the latest year."
        )
        if mort_trend_phrase:
            sentence += f" Over the period, it {mort_trend_phrase}."
        if isinstance(mort_delta, str) and mort_delta:
            sentence += f" That is {mort_delta.replace(' vs', ' since')}."
        paragraphs.append(sentence)

    # Income gap sentence
    if gap_val != "—":
        sentence = (
            f"In the **latest survey year**"
            f"{f' ({gap_year})' if gap_year else ''}, women under 50 in the highest income quintile (Q5) "
            f"report higher X-ray exam uptake than those in Q1 by about **{gap_val}**."
        )
        paragraphs.append(sentence)

    if not paragraphs:
        paragraphs = [
            "The current filters do not yield enough comparable data to generate a summary. Try widening the year range or adding more countries."
        ]

    for p in paragraphs:
        st.markdown(p)

    # ---------------- Caveats & Next steps ----------------
    st.markdown("### Limitations")
    st.markdown(
        """
        - Cross-country comparability depends on each country’s program organization, survey coverage, and reporting windows.
        - Self-reported examinations (survey) are a **2019 snapshot** in most cases; they are not a time series.
        - Under-50 mortality uses **age-specific rows when present**; otherwise TOTAL is used as a fallback, which can dilute the signal.
        - Correlations here **do not imply causation**; this dashboard is for awareness and discussion, not clinical guidance.
        """
    )

    st.markdown("### What to explore next")
    st.markdown(
        """
        - Compare **screening uptake change** vs **mortality change** over matched periods country-by-country.
        - Look at **participation by first-time invite vs recall** (if/when available) to refine age-of-entry effects.
        - Add **policy timeline annotations** (e.g., guideline updates) to give context to inflection points.
        - Enrich with **stage at diagnosis** (if open data exists) to connect screening to earlier detection.
        """
    )

    # ---------------- Downloads ----------------
    st.markdown("### Download your filtered data")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if not scr_f.empty:
            csv = scr_f.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Screening (CSV)", data=csv, file_name="screening_filtered.csv", mime="text/csv")
        else:
            st.button("Screening (no data)", disabled=True)
    with col_b:
        if not mort_f.empty:
            csv = mort_f.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Mortality (CSV)", data=csv, file_name="mortality_filtered.csv", mime="text/csv")
        else:
            st.button("Mortality (no data)", disabled=True)
    with col_c:
        if not exam_f.empty:
            csv = exam_f.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Exam by income (CSV)", data=csv, file_name="exam_income_filtered.csv", mime="text/csv")
        else:
            st.button("Exam by income (no data)", disabled=True)

    # ---------------- Notes ----------------
    st.markdown("### Notes on methods")
    st.markdown(
        """
        - KPIs use **medians across the selected countries** to reduce outlier impact.
        - Deltas compare the **first** and **last** year in the chosen range, not fixed calendar endpoints.
        - Income gap = median(Q5) − median(Q1) for women **under 50** in the latest survey year available within the selection.
        - Mini-trends plot medians across the selected countries for each year in range.
        """
    )
