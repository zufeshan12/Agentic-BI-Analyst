from pydantic import BaseModel,Field

#Schema for generator llm for structured and executable code generation.
class ChartCode(BaseModel):
    """Structured format for LLM-generated chart code."""
    code: str = Field(..., description="Valid Python code inside <execute_python>...</execute_python> tags")