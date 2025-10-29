from typing import TypedDict,Optional,Annotated

# create analyst state schema
class AnalystState(TypedDict):
    user_query : str
    data: dict
    schema: dict
    max_retry: int 
    rubric : Optional[list[dict[str,any]]]
    chart_code: Optional[str]
    chart_path: Optional[list[str]]