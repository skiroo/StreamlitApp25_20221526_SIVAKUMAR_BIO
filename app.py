# ==================================================
#                      Imports
# ==================================================
import streamlit as st
from utils.io import load_data


# ==================================================
#                    Page config
# ==================================================
st.set_page_config(
    page_title="The Age of Risk - Breast Cancer Awareness",
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

/* Header bar (top, where Deploy lives) */
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
.js-plotly-plot, .vega-embed, .stImage {
  background: var(--card) !important; border-radius: 12px; padding: 8px; border: 1px solid var(--border);
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



# ==================================================
#                      Sidebar
# ==================================================
st.sidebar.markdown("### Breast Cancer Awareness")


# ==================================================
#                   Main sections
# ==================================================
