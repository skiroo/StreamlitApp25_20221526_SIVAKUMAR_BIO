import pandas as pd

# === Breast cancer screening ===
def clean_screening(path='data/breast_cancer_screening.csv'):
    """
    Cleans the breast cancer screening dataset based on the exploration findings.

    Steps:
        1. Drop irrelevant or mostly missing columns: DATAFLOW, LAST UPDATE, freq, CONF_STATUS, OBS_FLAG.
        2. Keep only rows related to breast cancer (icd10 == 'C50').
        3. Keep only organized screening programs (source == 'PRG').
        4. Rename columns for clarity.
        5. Reset index and sort by country and year.

    Returns:
        Cleaned pandas DataFrame with columns:
        ['country', 'year', 'unit', 'source', 'icd10', 'screening_rate']
    """

    # Load the dataset
    df = pd.read_csv(path)

    # Drop irrelevant columns
    df = df.drop(columns=['DATAFLOW', 'LAST UPDATE', 'freq', 'CONF_STATUS', 'OBS_FLAG'], errors='ignore')

    # Keep only breast cancer (C50)
    df = df[df['icd10'] == 'C50']

    # Keep only organized screening programs (PRG)
    df = df[df['source'] == 'PRG']

    # Rename columns for clarity
    df = df.rename(columns={
        'geo': 'country',
        'TIME_PERIOD': 'year',
        'OBS_VALUE': 'screening_rate'
    })

    # Keep only relevant columns
    df = df[['country', 'year', 'unit', 'source', 'icd10', 'screening_rate']]

    # Convert data types
    df['year'] = df['year'].astype(int)
    df['screening_rate'] = pd.to_numeric(df['screening_rate'], errors='coerce')

    # Sort and reset index
    df = df.sort_values(by=['country', 'year']).reset_index(drop=True)

    return df


# === Death due to cancer ===
def clean_mortality(path='data/death_due_to_cancer.csv'):
    """
    Cleans the death rate by cancer dataset based on the updated exploration findings.

    Steps:
        1. Drop irrelevant or mostly missing columns: DATAFLOW, LAST UPDATE, freq, CONF_STATUS, OBS_FLAG.
        2. Keep only female records (sex == 'F').
        3. Keep only breast cancer data (icd10 == 'C50').
        4. Rename columns for clarity.
        5. Keep only relevant analytical columns.
        6. Convert data types and sort for consistency.

    Returns:
        Cleaned pandas DataFrame with columns:
        ['country', 'year', 'unit', 'age', 'sex', 'icd10', 'mortality_rate']
    """

    import pandas as pd

    # Load dataset
    df = pd.read_csv(path)

    # Drop irrelevant or mostly missing columns
    df = df.drop(columns=['DATAFLOW', 'LAST UPDATE', 'freq', 'CONF_STATUS', 'OBS_FLAG'], errors='ignore')

    # Keep only female data
    df = df[df['sex'].astype(str).str.upper().str.contains('F', na=False)]

    # Keep only breast cancer (C50)
    df = df[df['icd10'].astype(str).str.upper().str.contains('C50', na=False)]

    # Rename columns for clarity
    df = df.rename(columns={
        'geo': 'country',
        'TIME_PERIOD': 'year',
        'OBS_VALUE': 'mortality_rate'
    })

    # Keep only relevant columns
    df = df[['country', 'year', 'unit', 'age', 'sex', 'icd10', 'mortality_rate']]

    # Convert data types
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
    df['mortality_rate'] = pd.to_numeric(df['mortality_rate'], errors='coerce')

    # Sort and reset index
    df = df.sort_values(by=['country', 'year']).reset_index(drop=True)

    return df


# === Breast exam by income  ===
def clean_exam_income(path='data/breast_exam_income.csv'):
    """
    Cleans the self-reported breast examination dataset based on the exploration findings.

    Steps:
        1. Drop irrelevant or mostly missing columns: DATAFLOW, LAST UPDATE, freq, CONF_STATUS, OBS_FLAG.
        2. Drop missing values in OBS_VALUE.
        3. Rename columns for clarity.
        4. Keep only relevant analytical columns.
        5. Convert data types.
        6. Sort and reset index.

    Returns:
        Cleaned pandas DataFrame with columns:
        ['country', 'year', 'duration', 'age_group', 'income_quintile', 'unit', 'exam_rate']
    """

    # Load dataset
    df = pd.read_csv(path)

    # Drop irrelevant or mostly missing columns
    df = df.drop(columns=['DATAFLOW', 'LAST UPDATE', 'freq', 'CONF_STATUS', 'OBS_FLAG'], errors='ignore')

    # Drop rows with missing exam rate
    df = df.dropna(subset=['OBS_VALUE'])

    # Rename columns for clarity
    df = df.rename(columns={
        'geo': 'country',
        'TIME_PERIOD': 'year',
        'age': 'age_group',
        'quant_inc': 'income_quintile',
        'OBS_VALUE': 'exam_rate'
    })

    # Keep only relevant columns
    df = df[['country', 'year', 'duration', 'age_group', 'income_quintile', 'unit', 'exam_rate']]

    # Convert data types
    df['year'] = df['year'].astype(int)
    df['exam_rate'] = pd.to_numeric(df['exam_rate'], errors='coerce')

    # Sort and reset index
    df = df.sort_values(by=['country', 'income_quintile']).reset_index(drop=True)

    return df
