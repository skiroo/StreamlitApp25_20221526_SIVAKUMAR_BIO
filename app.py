# import libraries
import streamlit as st 
import pandas as pd 
from utils.io import load_data 
from utils.prep import make_tables 
from utils.viz import line_chart, bar_chart, map_chart

st.set_page_config(page_title="Data Storytelling Dashboard", layout="wide") 
 
@st.cache_data(show_spinner=False) 
def get_data(): 
    df_raw = load_data() 
    tables = make_tables(df_raw) 
    return df_raw, tables 
 
st.title("Data Storytelling: <Your Topic>") 
st.caption("Source: <dataset title> — <portal> — <license>") 
 
with st.sidebar: 
    st.header("Filters") 
    regions = st.multiselect("Region", []) 
    date_range = st.date_input("Date range", []) 
    metric = st.selectbox("Metric", []) 
 
raw, tables = get_data() 
 
# KPI row 
c1, c2, c3 = st.columns(3) 
c1.metric("KPI 1", "...", "∆ vs. baseline") 
c2.metric("KPI 2", "...") 
c3.metric("KPI 3", "...") 
 
st.subheader("Trends over time") 
line_chart(tables["timeseries"])  # custom function adds consistent styling 
 
st.subheader("Compare regions") 
bar_chart(tables["by_region"]) 
 
st.subheader("Map view") 
map_chart(tables["geo"]) 
 
st.markdown("### Data Quality & Limitations") 
st.info("Describe missing data, measurement limits, and biases.") 
 
st.markdown("### Key Insights & Next Steps") 
st.success("Summarize what matters and what actions follow.")