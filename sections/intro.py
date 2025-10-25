import streamlit as st
import pandas as pd
from pathlib import Path

# Intro section for: “The Age of Risk: When Should We Really Start Screening?”
_LOGO_PATH = Path("assets/pink-ribbon-logo.webp")

def render_intro(df_screening: pd.DataFrame | None = None,
                 df_mortality: pd.DataFrame | None = None,
                 df_exam_income: pd.DataFrame | None = None) -> None:

    # ===== Local CSS for the intro =====
    st.markdown(
        """
        <style>
        .intro-logo { display:block; width:100%; height:auto; }
        /* Make expanders more visible and move arrow next to title */
        [data-testid="stExpander"] > details {
            border: 1px solid var(--border); border-radius: 12px; background: var(--card);
        }
        [data-testid="stExpander"] summary {
            list-style: none; padding: 0.9rem 1rem; font-weight: 600; color: var(--text);
            display: flex; align-items: center; gap: 8px;
        }
        /* Hide default marker and add our own arrow left of the text */
        [data-testid="stExpander"] summary::-webkit-details-marker { display: none; }
        [data-testid="stExpander"] summary:before { content: "▸"; }
        [data-testid="stExpander"] > details[open] summary:before { content: "▾"; }
        /* Expander body */
        [data-testid="stExpander"] .stMarkdown { padding: 0 1rem 1rem 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===== Header / Branding =====
    c1, c2 = st.columns([1, 6])
    with c1:
        if _LOGO_PATH.exists():
            st.image(str(_LOGO_PATH), caption="Breast Cancer Awareness")
    with c2:
        st.title("The Age of Risk: When Should We Really Start Screening?")
        st.caption("Open data storytelling with Eurostat datasets")
        st.markdown(
            """
            I chose this topic now because October is Breast Cancer Awareness Month. Public attention is already focused on detection and prevention, which makes this a timely moment to examine whether our assumptions still hold.
            """
        )

    # ===== Hook =====
    st.markdown(
        """
        **Hook**
        
        She was 34. The guidance did not yet recommend routine screening for her age group. Months later, a diagnosis arrived at a later stage than anyone wanted. Stories like hers are not isolated. Across parts of Europe, data points to a quiet shift: a rising share of cases among women in their thirties and early forties. This dashboard asks a simple question with complex implications: if risk is changing for younger women, should screening policy and messaging change too?
        """
    )

    # ===== Audience & Questions =====
    with st.expander("Audience and key questions", expanded=True):
        st.markdown(
            """
            **Audience:** Public health professionals, policy makers, and citizens interested in women's health.

            **Key questions:**
            1. Are younger women aged 30 to 45 increasingly affected by breast cancer?
            2. How do screening participation rates differ below 50 compared with the recommended screening ages?
            3. Do income differences compound the gap in early examination for younger women?
            """
        )

    # ===== About =====
    st.subheader("About this project")
    st.markdown(
        """
        This dashboard uses open data from Eurostat to compare screening participation, mortality, and self-reported examinations by age and income across European countries. The goal is to surface patterns that can inform awareness strategies and policy discussion.
        """
    )

    # ===== Data sources =====
    with st.expander("Datasets used", expanded=False):
        st.markdown(
            """
            **1. Breast cancer and cervical cancer screenings, 2000 to 2021**  
            Publisher: Eurostat  
            Participation in organized mammography by country and age group.  
            Use: line chart of screening rates over time for 40 to 49 versus 50 to 69, and a map comparison.  
            [https://data.europa.eu/data/datasets/75kk9hje0s7cm2idhpvvww?locale=en](https://data.europa.eu/data/datasets/75kk9hje0s7cm2idhpvvww?locale=en)

            **2. Death due to cancer, by sex, 2000 to 2021**  
            Publisher: Eurostat  
            Standardized mortality per 100,000 for breast cancer (ICD-10 C50).  
            Use: mortality trend lines and KPIs, with attention to under 50 where available.  
            [https://ec.europa.eu/eurostat/databrowser/view/hlth_cd_asdr2__custom_18611676/default/table](https://ec.europa.eu/eurostat/databrowser/view/hlth_cd_asdr2__custom_18611676/default/table)

            **3. Self-reported last breast examination by X-ray among women by age and income quintile**  
            Publisher: Eurostat  
            Age and income breakdowns of mammography participation.  
            Use: bar chart to show lower participation among younger and lower-income women.  
            [https://data.europa.eu/data/datasets/otvi02wdhgtfmmgvvkvgxa?locale=en](https://data.europa.eu/data/datasets/otvi02wdhgtfmmgvvkvgxa?locale=en)
            """
        )


    # ===== Lightweight coverage KPIs =====
    def _meta_stats(df: pd.DataFrame | None, col="year"):
        if df is None or df.empty or col not in df.columns:
            return ""
        return f"{int(df[col].min())} to {int(df[col].max())}"

    years_screen = _meta_stats(df_screening)
    years_mort = _meta_stats(df_mortality)
    years_income = _meta_stats(df_exam_income)

    countries = set()
    for d in (df_screening, df_mortality, df_exam_income):
        if isinstance(d, pd.DataFrame) and not d.empty and "country" in d.columns:
            countries.update(d["country"].dropna().unique().tolist())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Countries covered", f"{len(countries)}")
    k2.metric("Screening years", years_screen or "")
    k3.metric("Mortality years", years_mort or "")
    k4.metric("Income survey years", years_income or "")

    # ===== Narrative approach =====
    st.subheader("Narrative approach")
    st.markdown(
        """
        1. Hook: a personal and data-grounded entry point.
        2. Analyze: show rising burden among women aged 30 to 45.
        3. Compare: screening eligibility starting at 50 versus actual diagnosis distribution.
        4. Insight: a growing share of diagnoses is below the current screening age.
        5. Implication: guidelines and messaging may need to be reassessed.
        """
    )

    # ===== Ethics and data quality =====
    st.subheader("Ethics and data quality")
    st.info(
        """
        - Data are aggregated public statistics with no personal identifiers.
        - Methods and reporting windows differ by country, so comparisons require caution.
        - Trends and correlations do not imply causation and should not be taken as clinical guidance.
        - The aim is to support informed public discussion and further research.
        """
    )

    st.caption("Prepared by Kiroshan SIVAKUMAR - EFREI Paris. For academic use only.")
