# The Age of Risk: When Should We Really Start Screening?
**Open data storytelling with Eurostat datasets — Streamlit app**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff4b4b.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> October is Breast Cancer Awareness Month. Public attention is already focused on detection and prevention, which makes this a timely moment to examine whether our assumptions still hold.  
> This app explores **screening participation**, **mortality**, and **income-linked disparities** across Europe to ask:  
> **If risk is shifting for younger women (30–45), should screening policy and messaging change too?**

**Live app:**  [**`<ADD_DEPLOYED_URL_HERE>`**](#)  
**Repository:** [github.com/skiroo/StreamlitApp25_20221526_SIVAKUMAR_BIO](https://github.com/skiroo/StreamlitApp25_20221526_SIVAKUMAR_BIO)

---

## What’s inside

- **Intro** — context, audience, datasets, ethics  
- **Overview** — sidebar filters; KPIs; screening & mortality trends; income gap (Q5−Q1) for <50  
- **Deep dives** — country focus; age bands (40–49 vs 50–69); under-50 burden; income×age heatmap; **interactive trends**; **Europe choropleth map**  
- **Conclusion** — key takeaways, limitations, next steps, and **download** buttons for filtered data  

All visuals are styled consistently (clean borders) and most are interactive (hover, legend select, brush to zoom).  
Maps use Plotly; the rest use Altair.

---

## Project structure

```plaintext
StreamlitApp25_20221526_SIVAKUMAR_BIO/
├─ app.py                     # Main entry point
├─ sections/
│  ├─ intro.py                # Landing & context
│  ├─ overview.py             # KPIs + trends + income gap
│  ├─ deep_dives.py           # Interactive charts + Europe map
│  ├─ conclusion.py           # Final KPIs, sparklines & downloads
├─ data/                      # CSVs (ignored from git if large)
│  ├─ breast_cancer_screening.csv
│  ├─ death_due_to_cancer.csv
│  └─ breast_exam_income.csv
├─ prep.py                    # Cleaning & standardization helpers
├─ requirements.txt           # Python dependencies
└─ README.md
```
