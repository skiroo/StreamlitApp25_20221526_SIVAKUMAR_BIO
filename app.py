# ==================================================
#                      Imports
# ==================================================
import streamlit as st
from utils.io import load_data
from sections.intro import render_intro
from sections.overview import render_overview
from sections.deep_dives import render_deep_dives
from sections.conclusion import render_conclusion

# ==================================================
#                    Page config
# ==================================================
st.set_page_config(
    page_title="The Age of Risk | Breast Cancer Screening",
    page_icon="assets/pink-ribbon-logo.webp",
    layout="wide"
)

# ==================================================
#                        CSS
# ==================================================
st.markdown("""
<style>
:root{
  /* Core palette */
  --bg: #ffe9f0;            /* light pink page background */
  --sidebar: #f7c1d4;       /* darker sidebar panel */
  --header: #ffd6e4;        /* header bar color */
  --card: #fff8fb;          /* chart containers and cards */
  --text: #3a0b1a;          /* primary text (dark rose) */
  --muted: #6c3c4c;         /* secondary text */
  --accent: #e91e63;        /* ribbon pink */
  --accent-dark: #c2185b;   /* deeper pink for hover */
  --chip: #f6cfe0;          /* chip background */
  --chip-text: #5a2540;     /* chip text */
  --border: #f1b8ca;        /* soft borders */
}

/* Global surfaces and type */
html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; }
h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }
p, span, div, label { color: var(--text) !important; }

/* Header bar */
[data-testid="stHeader"] { background: var(--header) !important; }
[data-testid="stHeader"] * { color: var(--text) !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--sidebar) !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebarNav"] { background: transparent !important; }

/* Center the logo in sidebar */
.sidebar-logo-wrap { text-align: center; margin-top: 4px; margin-bottom: 10px; }

/* Inputs */
.stSelectbox div[data-baseweb="select"] > div {
  background: var(--card) !important; color: var(--text) !important; border: 1px solid var(--border);
}
.stTextInput>div>div>input, .stNumberInput>div>div input { background: var(--card) !important; color: var(--text) !important; }
.stSlider > div > div > div { background: var(--accent) !important; }
.stSlider [data-baseweb="slider"] div[role="slider"] { border: 2px solid var(--chip) !important; background: var(--accent) !important; }

/* Buttons */
.stButton>button {
  background: var(--accent) !important; color: white !important; border: 0 !important;
  border-radius: 10px !important; padding: 0.5rem 0.9rem !important;
}
.stButton>button:hover { background: var(--accent-dark) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  border-bottom: 3px solid var(--accent) !important; color: var(--accent) !important;
}

/* Metrics */
[data-testid="stMetric"] { background: var(--card); padding: 12px; border-radius: 12px; border: 1px solid var(--border); }
[data-testid="stMetricValue"] { color: var(--text) !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; }
[data-testid="stMetricDelta"] { color: var(--accent-dark) !important; }

/* Chips and callouts */
.ribbon-border { border-left: 6px solid var(--accent); padding-left: 12px; }
.pink-chip { background: var(--chip); color: var(--chip-text); padding: 4px 10px; border-radius: 999px; font-weight: 600; display: inline-block; margin-right: 8px; }

/* Chart containers */
.stPlotlyChart, [data-testid="stAltairChart"]{
  background: var(--card) !important;
  border-radius: 12px;
  padding: 8px;
  border: 1px solid var(--border);
}

/* Let Plotly handle its own background; ensure transparency */
.js-plotly-plot {
  background: transparent !important;
  padding: 0 !important;
}

/* Dataframes */
.stDataFrame { background: var(--card) !important; border-radius: 8px; }

/* Footnotes and captions */
.stCaption, .caption, small { color: var(--muted) !important; }

/* Horizontal rules */
hr { border: 0; border-top: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

# ==================================================
#                     Load data
# ==================================================
df_screening, df_mortality, df_exam_income = load_data()

# Country code → human name (used in sidebar labels)
CODE_TO_NAME = {
    "FR":"France","BE":"Belgium","DE":"Germany","ES":"Spain","IT":"Italy","PT":"Portugal",
    "IE":"Ireland","NL":"Netherlands","LU":"Luxembourg","AT":"Austria","CH":"Switzerland",
    "GB":"United Kingdom","UK":"United Kingdom","SE":"Sweden","NO":"Norway","FI":"Finland","DK":"Denmark",
    "IS":"Iceland","EE":"Estonia","LV":"Latvia","LT":"Lithuania","PL":"Poland","CZ":"Czechia","SK":"Slovakia",
    "HU":"Hungary","SI":"Slovenia","HR":"Croatia","RO":"Romania","BG":"Bulgaria","GR":"Greece","EL":"Greece",
    "CY":"Cyprus","MT":"Malta","AL":"Albania","BA":"Bosnia and Herzegovina","ME":"Montenegro","RS":"Serbia",
    "MK":"North Macedonia"
}
NAME_TO_CODE = {v:k for k,v in CODE_TO_NAME.items()}

# ==================================================
#                      Sidebar  (GLOBAL FILTERS)
# ==================================================
import pandas as pd

with st.sidebar:
    st.image("assets/pink-ribbon-logo.webp")
    st.markdown("### Global filters")

    # Countries available from any table
    codes = set()
    for d in (df_screening, df_mortality, df_exam_income):
        if isinstance(d, pd.DataFrame) and not d.empty and "country" in d.columns:
            codes.update(d["country"].dropna().astype(str).tolist())
    codes = sorted(codes)
    names = sorted([CODE_TO_NAME.get(c, c) for c in codes])

    # Default = France if present
    default_names = ["France"] if "France" in names else (names[:1] if names else [])
    sel_names = st.multiselect("Countries", names, default=default_names, key="global_countries")
    sel_codes = [NAME_TO_CODE.get(n, n) for n in sel_names]
    if not sel_codes:
        sel_codes = ["FR"]

    # Year bounds
    years = []
    for d in (df_screening, df_mortality, df_exam_income):
        if isinstance(d, pd.DataFrame) and not d.empty and "year" in d.columns:
            years += pd.to_numeric(d["year"], errors="coerce").dropna().tolist()
    ymin = int(min(years)) if years else None
    ymax = int(max(years)) if years else None
    y0, y1 = (st.slider("Year range", ymin, ymax, (ymin, ymax), key="global_years")
              if (ymin is not None and ymax is not None) else (None, None))

# Make filters available to all sections
st.session_state["global_filters"] = {"countries": sel_codes, "y0": y0, "y1": y1, "code_to_name": CODE_TO_NAME}

# ==================================================
#                   Main sections
# ==================================================
render_intro(df_screening, df_mortality, df_exam_income)
render_overview(df_screening, df_mortality, df_exam_income)
render_deep_dives(df_screening, df_mortality, df_exam_income)
render_conclusion(df_screening, df_mortality, df_exam_income)
