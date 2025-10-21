import pandas as pd
import re

def load_csv_data(file_path):
    """load csv into pandas Dataframe and return df with schema"""
    df = pd.read_csv(file_path)
    schema = df.dtypes.to_dict()
    return df,schema

def extract_python_code(code_string:str) -> str:
    match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", code_string)
    if match:
        code = match.group(1).strip()
    return code
    