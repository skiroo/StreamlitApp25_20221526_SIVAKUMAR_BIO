# The Age of Risk: When Should We Really Start Screening?

**Author:** Kiroshan SIVAKUMAR  
**Institution:** EFREI Paris  
**Course:** Data Visualization – Individual Student Project  
**Instructor:** Mano Joseph Mathew  
**Framework:** Streamlit

---

## Project Links

- **GitHub Repository:** [https://github.com/skiroo/StreamlitApp25_20221526_SIVAKUMAR_BIO](https://github.com/skiroo/StreamlitApp25_20221526_SIVAKUMAR_BIO.git)  
- **Live Dashboard:** [https://breast-cancer-storytelling-dashboard.streamlit.app/](https://breast-cancer-storytelling-dashboard.streamlit.app/)

---

## Project Overview

This Streamlit dashboard explores **breast cancer screening patterns** across European countries, using open data from **Eurostat**.  
It aims to answer one critical question:

> If risk is increasing among younger women, should screening guidelines and awareness efforts begin earlier?

The project connects three complementary datasets to tell a data-driven story about **age, income, and mortality trends** related to breast cancer.

---

## Objectives

- Highlight disparities in **screening participation** between age groups (under 50 vs. 50–69).  
- Examine trends in **mortality rates** among younger women.  
- Assess how **income levels** influence the likelihood of early breast exams.  
- Promote awareness during **Breast Cancer Awareness Month (October)** through an evidence-based visual story.

---

## Datasets Used

| # | Dataset Title | Source | Description |
|---|----------------|--------|-------------|
| 1 | **Breast cancer and cervical cancer screenings (2000–2021)** | [Eurostat](https://data.europa.eu/data/datasets/75kk9hje0s7cm2idhpvvww?locale=en) | Participation in organized mammography programs by country and age group. |
| 2 | **Death due to cancer by sex (2000–2021)** | [Eurostat](https://ec.europa.eu/eurostat/databrowser/view/hlth_cd_asdr2__custom_18611676/default/table) | Standardized mortality per 100,000 for breast cancer (ICD-10 C50). |
| 3 | **Self-reported last breast examination by X-ray** | [Eurostat](https://data.europa.eu/data/datasets/otvi02wdhgtfmmgvvkvgxa?locale=en) | Breakdown by age and income quintile to highlight participation inequality. |

All datasets are aggregated public data with no personal identifiers.

---

## Narrative Flow

1. **Hook:**  
   “She was 34. The guidance did not yet recommend screening for her age group...”  

2. **Overview:**  
   KPIs and key trends showing participation and mortality rates.  

3. **Deep Dives:**  
   Compare across countries, age bands, and income levels with interactive charts and a Europe map.  

4. **Conclusion:**  
   Summarize findings, limitations, and next steps for research or policy.

---

## Installation and Usage

### 1. Requirements

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Recommended packages include:
```txt
streamlit
pandas
altair
plotly
```

### 2. Run the App

```bash
streamlit run app.py
```

### 3. Folder Structure

```bash
├── app.py
├── utils/
│   ├── io.py
│   ├── prep.py
│   ├── viz.py
│   └── exploration.ipynb
├── sections/
│   ├── intro.py
│   ├── overview.py
│   ├── deep_dives.py
│   └── conclusion.py
├── data/
│   ├── breast_cancer_screening.csv
│   ├── death_due_to_cancer.csv
│   └── breast_exam_income.csv
└── assets/
    └── pink-ribbon-logo.webp
```

---

## Features

- Four main sections: Introduction, Overview, Deep Dives, and Conclusion.  
- Custom pink-themed UI inspired by the Pink Ribbon campaign.  
- Interactive visuals built with Altair and Plotly:
  - Line charts, bar charts, heatmaps, and a choropleth map of Europe.  
- Dynamic filters in the sidebar for country and year range.  
- KPIs summarizing screening, mortality, and income gap metrics.  
- Download options for filtered datasets.  

---

## Data Exploration and Cleaning

The file `utils/exploration.ipynb` was used to **explore and understand the datasets** prior to cleaning.  
This notebook contains initial data inspection steps such as checking missing values, column relevance, and year coverage across countries.  
Based on these findings, the data cleaning logic was implemented in `utils/prep.py`, which:

- Removes irrelevant or mostly empty columns.  
- Keeps only female and breast cancer (ICD-10 C50) records.  
- Focuses on organized screening programs (`source == 'PRG'`).  
- Renames and standardizes column names.  
- Ensures consistent numeric and temporal formats across datasets.  

The cleaned data is then loaded using `utils/io.py`.

---

## Insights and Takeaways

- Median **organized screening rates** have improved over time in most countries.  
- However, **mortality among women under 50** remains significant.  
- There is a **clear income-based disparity**: women in the top quintile (Q5) are much more likely to report a breast exam than those in Q1.  
- Together, these patterns suggest a need to **reassess awareness strategies and screening age thresholds**.

---

## Limitations

- Cross-country comparisons depend on reporting consistency and program coverage.  
- Survey data (examinations) are snapshots, not continuous time series.  
- Correlation does not imply causation — this dashboard is for public awareness, not clinical recommendations.

---

## License and Acknowledgments

- Data © Eurostat, open for academic and non-commercial use.  
- Project created as part of the **#EFREIDataStories2025** initiative.  
- Logo and color palette inspired by the **Pink Ribbon** campaign.

---

## Citation

> SIVAKUMAR, Kiroshan. *The Age of Risk: When Should We Really Start Screening?*  
> EFREI Paris, Data Visualization Project (2025).  
> Using Eurostat open data for educational purposes.
