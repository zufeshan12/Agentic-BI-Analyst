from pydantic import BaseModel,Field
from typing import Literal

#Schema for evaluator llm (LLM-as-judge) for consistent, rubric-aligned, and actionable feedback.
class EvaluationCriteria(BaseModel):
    """Structured format for evaluating LLM-generated chart code"""
    relevance: Literal[1,0] = Field(...,description="Does this chart address the user query accurately?")
    correct_data_mapping: Literal[1,0] = Field(...,description="Are the axes and data encodings correct?")
    appropriate_chart_type: Literal[1,0] = Field(...,description="Is the chart type appropriate for the data and query?")
    feedback: str = Field(...,description="a brief feedback on the chart not exceeding a paragraph")
