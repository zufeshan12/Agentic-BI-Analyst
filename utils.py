import pandas as pd
import base64
from PIL import Image
from io import BytesIO
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
    
def encode_image_b64(path: str) -> str:
    """Return base64_str for an image file path."""
    img = Image.open(path)
    img = img.convert("RGB")
    img.thumbnail((512, 512))  # resize to manageable dimensions
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")