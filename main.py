from fastapi import FastAPI, UploadFile, Form,Path,File,HTTPException
from fastapi.responses import JSONResponse,FileResponse
import pandas as pd
import io
import os
from typing import Optional
from agent_backend import run_workflow 
from schema.analyst_state_schema import AnalystState
from schema.evaluation_rubric_schema import EvaluationCriteria
from utils import *    

app = FastAPI(title="Agentic BI Analyst API")

@app.get("/")
def welcome():
    return {"message":"Hello! Welcome to Agentic BI Analyst"}

@app.get("/health")
def healthcheck():
    return {"status": "OK",
            "version": "1.0"
            }

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...,description="CSV file to analyze"),
    user_query: str = Form(...,description="User query to plot a chart"),
    max_retry: Optional[int] = Form(description="No. of retries in case of error or feedback",default=3,ge=1,le=7)
):
    """
    Upload a CSV, specify a text query and max retry limit.
    Returns the generated charts and rubric feedback.
    """
    try:
        # Load CSV into pandas DataFrame
        contents = await file.read()
        
        # Extract schema and convert df to dict for LLM consumption
        df,schema = load_csv_data(io.BytesIO(contents)) 
        #data = df.head(5).to_dict(orient="records")
        data = df.to_dict(orient="records")

        # Define initial state
        initial_state: AnalystState = {
            "user_query": user_query,
            "data": data,
            "schema": schema,
            "max_retry": max_retry,
            "rubric": None,
            "chart_code": None,
            "chart_path": None,
        }

        # Run the LangGraph workflow
        final_state = run_workflow(initial_state)

        # Serialize rubric for readability (convert Pydantic -> dict)
        #rubric_list = serialize_rubric(final_state.get("rubric"), final_state)
        #print(rubric_list)

        # Prepare response
        response = {
            "query": user_query,
            "charts": final_state.get("chart_path"),
            "rubric_feedback": final_state.get("rubric")
        }

        return JSONResponse(status_code=200,content={'response':response})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/charts/{chart_path}")
def display_chart(chart_path:str = Path(...,description="Name of the chart file",example="chart_v0.png")):
    """Display chart as image if present"""

    file_path = os.path.join("charts",chart_path)
    # check if file exists
    if os.path.exists(file_path):
        # display chart
        return FileResponse(path=file_path,media_type="image/png")
    else:
        return JSONResponse(status_code=404,content={"error":"Chart not found."})
    
#@app.delete("/charts/delete")
