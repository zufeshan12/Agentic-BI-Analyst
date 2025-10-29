import pandas as pd
import base64
from PIL import Image
from io import BytesIO
from schema.analyst_state_schema import AnalystState
from schema.evaluation_rubric_schema import EvaluationCriteria
import re
import os

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

def serialize_rubric(response:EvaluationCriteria,state:AnalystState) -> list[dict]:
    """Convert rubric from pydantic object to a serializable object like json or dict"""

    if hasattr(response,"model_dump"):
        serialized = response.model_dump()
    elif hasattr(response,"dict"):
        serialized = response.dict()
    else:
        serialized = response
    
    rubric_list = state.get("rubric") or []
    rubric_list.append(serialized)
    state["rubric"] = rubric_list

    return rubric_list

def clear_charts():
    """Empty the Charts folder before new request"""
    dir_path = "charts"
    if os.path.exists(dir_path):
        for file in os.listdir(dir_path):
            
            file_path = os.path.join(dir_path,file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
