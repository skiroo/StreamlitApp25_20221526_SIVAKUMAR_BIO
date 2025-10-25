# sections/overview.py
import streamlit as st
import pandas as pd
import altair as alt
import re
from typing import Iterable


# =====------ Utilities =====------
def _coerce_year(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def _year_bounds(dfs: Iterable[pd.DataFrame]) -> tuple[int | None, int | None]:
    years = []
    for d in dfs:
        if isinstance(d, pd.DataFrame) and "year" in d.columns:
            years.extend(pd.to_numeric(d["year"], errors="coerce").dropna().unique().tolist())
    if not years:
        return None, None
    return int(min(years)), int(max(years))


def _default_countries(dfs: Iterable[pd.DataFrame], k: int = 6) -> list[str]:
    counts = {}
    for d in dfs:
        if isinstance(d, pd.DataFrame) and "country" in d.columns:
            vc = d["country"].dropna().value_counts()
            for country, n in vc.items():
                counts[country] = counts.get(country, 0) + int(n)
    return [c for c, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:k]]


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
    if m:
        return f"Q{m.group(2)}"
    if re.fullmatch(r"[1-5]", s):
        return f"Q{s}"
    if re.search(r"(LOWEST|FIRST|BOTTOM)\b", s):
        return "Q1"
    if re.search(r"\bSECOND\b", s):
        return "Q2"
    if re.search(r"\bTHIRD\b", s):
        return "Q3"
    if re.search(r"\bFOURTH\b", s):
        return "Q4"
    if re.search(r"(HIGHEST|FIFTH|TOP)\b", s):
        return "Q5"
    return None


def _income_q1_q5_sub50(df_exam_income: pd.DataFrame) -> pd.DataFrame:
    """
    Tolerant to:
      - income_quintile encoded as QU1..QU5 or Q1..Q5 or verbose labels
      - age groups expressed as Y-codes or plain ranges like 30-39, 40-49, 45-49
    """
    if df_exam_income is None or df_exam_income.empty:
        return df_exam_income

    d = df_exam_income.copy()

    # Canonicalize quintiles
    if "income_quintile" in d.columns:
        d["income_quintile"] = d["income_quintile"].apply(_canon_quintile)

    # Keep clearly under 50
    if "age_group" in d.columns:
        ag = d["age_group"].astype(str)
        sub50 = (
            ag.str.contains(
                r"Y1?5-24|Y25-34|Y30-39|Y35-44|Y40-44|Y40-49|Y45-49|Y_GE16_LT50|Y_LT50",
                regex=True,
                case=False,
            )
            | ag.str.contains(
                r"\b(15-24|25-34|30-39|35-44|40-44|40-49|45-49)\b",
                regex=True,
                case=False,
            )
        )
        d = d[sub50]

    # Keep Q1 and Q5 only
    if "income_quintile" in d.columns:
        d = d[d["income_quintile"].isin(["Q1", "Q5"])]

    return d


# =====------ Chart styling =====------
def _styled_chart(chart, title=None, height=340):
    """Apply a uniform border and clean axes to Altair charts."""
    return (
        chart.properties(
            title=title or "",
            width="container",
            height=height,
            background="white",
            padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        )
        .configure_view(
            stroke="lightgray",
            strokeWidth=1.2,
        )
        .configure_axis(
            grid=False,
            domainColor="lightgray",
            labelColor="#333",
            titleColor="#333",
        )
        .configure_title(
            anchor="start",
            fontSize=14,
            color="#222",
            fontWeight="bold",
        )
    )


# =====------ Render =====------
def render_overview(
    df_screening: pd.DataFrame | None = None,
    df_mortality: pd.DataFrame | None = None,
    df_exam_income: pd.DataFrame | None = None,
) -> None:
    """
    Overview section with KPIs and trends.

    Expected columns (after your cleaning):
      df_screening:  country, year, screening_rate
      df_mortality:  country, year, age, sex, icd10, mortality_rate
      df_exam_income: country, year, duration, age_group, income_quintile, unit, exam_rate
    """

    # Minimal styling for selection chips and h4 headers
    st.markdown(
        """
        <style>
        .pink-chip {
            display:inline-block; padding:0.18rem 0.5rem; margin:0 0.25rem 0.25rem 0;
            border-radius:999px; background:rgba(255, 105, 180, 0.12);
            border:1px solid rgba(255, 105, 180, 0.35); font-size:0.85rem;
        }
        .chip-row { margin-bottom: 0.25rem; }
        [data-testid="stMarkdownContainer"] h4 {
            background: #ffe6eb;
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Overview")

    # Defensive typing and year coercion
    df_screening = _coerce_year(df_screening)
    df_mortality = _coerce_year(df_mortality)
    df_exam_income = _coerce_year(df_exam_income)

    # Year bounds and default countries
    y_min, y_max = _year_bounds([df_screening, df_mortality, df_exam_income])
    default_ctrs = _default_countries([df_screening, df_mortality, df_exam_income])

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")
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
        countries = st.multiselect(
            "Countries",
            all_countries,
            default=default_ctrs if default_ctrs else all_countries[:6],
            key="ov_countries",
        )
        if y_min is not None and y_max is not None:
            y0, y1 = st.slider(
                "Year range",
                int(y_min),
                int(y_max),
                (int(y_min), int(y_max)),
                key="ov_years",
            )
        else:
            y0, y1 = None, None
            st.info("No year information in the loaded tables.")

    # Apply filters
    if y0 is not None:
        df_screening_f = _filter_years(_filter_countries(df_screening, countries), y0, y1)
        df_mortality_f = _filter_years(_filter_countries(df_mortality, countries), y0, y1)
        df_exam_income_f = _filter_years(_filter_countries(df_exam_income, countries), y0, y1)
    else:
        df_screening_f, df_mortality_f, df_exam_income_f = df_screening, df_mortality, df_exam_income

    # Show active filter chips
    if countries or y0 is not None:
        chips = " ".join([f'<span class="pink-chip">{c}</span>' for c in countries]) if countries else ""
        years_txt = f"{y0} to {y1}" if y0 is not None else "All years"
        st.markdown(f'<div class="chip-row">{chips}<span class="pink-chip">Years: {years_txt}</span></div>', unsafe_allow_html=True)

    # ===== KPIs =====
    k1, k2, k3 = st.columns(3)

    # KPI 1 Screening median latest, delta vs first
    scr_kpi = ""
    scr_delta = ""
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

    # KPI 2 Mortality median under 50 latest, delta vs first
    mort_kpi = ""
    mort_delta = ""
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

    # KPI 3 Income gap Q5 minus Q1 for under 50 latest survey year
    gap_val = ""
    gap_note = ""
    ei_sub = _income_q1_q5_sub50(df_exam_income_f)
    if ei_sub is not None and not ei_sub.empty and {"income_quintile", "exam_rate", "year"}.issubset(ei_sub.columns):
        last_year_e = ei_sub["year"].dropna().max()
        ei_last = ei_sub[ei_sub["year"].eq(last_year_e)]
        if not ei_last.empty:
            q5 = ei_last[ei_last["income_quintile"].eq("Q5")]["exam_rate"].median()
            q1 = ei_last[ei_last["income_quintile"].eq("Q1")]["exam_rate"].median()
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
        color = alt.Color("country:N", legend=alt.Legend(title="Country")) if countries and len(countries) > 1 else alt.value("#1f77b4")
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
        st.altair_chart(_styled_chart(line + rule, title=""), use_container_width=True)
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
        color = alt.Color("country:N", legend=alt.Legend(title="Country")) if countries and len(countries) > 1 else alt.value("#d62728")
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
        st.altair_chart(_styled_chart(line, title=""), use_container_width=True)
    else:
        st.info("Mortality table not available or missing mortality_rate.")

    # ===== Income inequality snapshot =====
    st.markdown("#### Income inequality snapshot in recent survey Q5 vs Q1, under 50")
    if ei_sub is not None and not ei_sub.empty and {"income_quintile", "exam_rate", "country", "year"}.issubset(ei_sub.columns):
        last_year_e = int(ei_sub["year"].dropna().max())
        ei_last = ei_sub[ei_sub["year"].eq(last_year_e)]

        wide = (
            ei_last.groupby(["country", "income_quintile"])["exam_rate"]
            .median()
            .unstack()  # columns will be like ['Q1', 'Q5'] after canonicalization
        )

        if set(["Q1", "Q5"]).issubset(wide.columns):
            gap_by_ctry = (
                wide.assign(gap=lambda d: d["Q5"] - d["Q1"])
                .reset_index()
                .dropna(subset=["gap"])
            )
            if countries:
                gap_by_ctry = gap_by_ctry[gap_by_ctry["country"].isin(countries)]

            if not gap_by_ctry.empty:
                bars = (
                    alt.Chart(gap_by_ctry)
                    .mark_bar()
                    .encode(
                        x=alt.X("gap:Q", title="Q5 minus Q1 percentage points"),
                        y=alt.Y("country:N", sort="-x", title="Country"),
                        tooltip=[
                            "country",
                            alt.Tooltip("Q1:Q", format=".1f"),
                            alt.Tooltip("Q5:Q", format=".1f"),
                            alt.Tooltip("gap:Q", format=".1f"),
                        ],
                    )
                )
                st.caption(f"Latest survey year in selection: {last_year_e}")
                st.altair_chart(_styled_chart(bars, title="", height=max(200, 28 * max(4, len(gap_by_ctry)))) , use_container_width=True)
            else:
                st.info("No Q1 vs Q5 comparison available for the selected countries in the latest survey year.")
        else:
            st.info("Q1 or Q5 is missing after canonicalization for the latest survey year.")
    else:
        st.info("Exam by income table not available or missing required columns.")

    # ===== Methods and caveats =====
    with st.expander("How these KPIs are computed", expanded=False):
        st.markdown(
            """
            - Screening KPI: median organized screening rate across selected countries in the latest available year, with a delta to the first year in range.
            - Mortality KPI: median female breast cancer mortality rate where age groups under 50 are available. If only TOTAL is present, it is used as a fallback.
            - Income gap KPI: median difference Q5 minus Q1 in self-reported last X-ray exam among women below 50 in the latest survey year.
            
            All visuals respect the country and year filters. Missing values are ignored in medians.
            """
        )
