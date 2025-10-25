import pandas as pd
from utils.prep import clean_screening, clean_mortality, clean_exam_income

def load_data():
    df_screening = clean_screening('data/breast_cancer_screening.csv')
    df_mortality = clean_mortality('data/death_due_to_cancer.csv')
    df_exam_income = clean_exam_income('data/breast_exam_income.csv')
    return df_screening, df_mortality, df_exam_income
