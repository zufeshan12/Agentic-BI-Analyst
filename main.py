from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate,load_prompt
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from langgraph.graph import StateGraph,START,END,add_messages
from langsmith import traceable
from pydantic import BaseModel,Field
from typing import Literal,Annotated,Optional,TypedDict
import pandas as pd
from schema.chart_code_schema import ChartCode
from schema.evaluation_rubric_schema import EvaluationCriteria
import warnings
from io import StringIO
from utils import *
from dotenv import load_dotenv

load_dotenv()

# create analyst state schema
class AnalystState(TypedDict):
    user_query : str
    data: dict
    schema: dict
    max_retry: int 
    rubric : Optional[list[dict[str,any]]]
    chart_code: Optional[str]
    chart_path: Optional[str]

@traceable(run_type="llm",name="generate chart code",tags=["chart_code","chart_path"])
def generate_chart_code(state:AnalystState) -> dict:
    """Generate/Revise chart code in python based on user query"""

    # load csv data as str as LLMs can handle textual descriptions of dicts — and load_prompt will accept them.
    user_query = state.get("user_query")
    #data = str(state.get("data"))
    schema = str(state.get("schema"))
    feedback = state["rubric"][-1]['feedback'] if state.get("rubric") else "No feedback yet. This is the first attempt."
    
    # file path to save generated chart
    out_path = f"charts/chart_{str(state['max_retry'])}.png"

    # define generator llm enforcing schema
    generator = generator_llm.with_structured_output(ChartCode)

    if user_query:
        prompt = load_prompt(path="prompts/generator_prompt.json") # load saved prompt
        # create a runnable to invoke 
        chain = RunnableSequence(prompt,generator)
        # invoke chain : prompt -> model -> response
        chart_code = chain.invoke({"user_query":user_query,
                                 "schema":schema,
                                 "feedback":feedback,
                                 "out_path_v1":out_path})
    
    return {"chart_code":chart_code.code,"chart_path":out_path}

@traceable(name="generate_chart",tags=["max_retry","rubric"])
def generate_chart(state:AnalystState):
    """Generate image/PNG from chart code"""

    chart_code = state.get("chart_code")
    rubric_list = state.get("rubric")
    feedback = None
    error = None
    
    if chart_code:
        # Extract the code within the <execute_python> tags
        chart_code = extract_python_code(chart_code)
        # If code runs successfully, the file chart_{max_retry}.png should have been generated
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                exec_globals = {"df":df}
                exec(chart_code,exec_globals)
            except Exception as e:
                feedback="Chart generation failed."
                error = str(e)
            else:
                if w:
                    feedback = "Warning detected: " + "; ".join(str(warn.message) for warn in w)
                    
    rubric = EvaluationCriteria(feedback=feedback,error=error)
    print(rubric)
    rubric_list = serialize_rubric(rubric,state)
    print(rubric_list)
    # update max_retry
    max_retry = state["max_retry"] - 1
    return {"max_retry":max_retry,"rubric":rubric_list}

@traceable(run_type="llm",name="evaluate_chart",tags=["rubric"])
def evaluate_chart(state:AnalystState):
    """Evaluate llm-generated chart code and generate appropriate rubric-aligned feedback"""

    user_query = state.get("user_query")
    data = str(state.get("data"))
    schema = str(state.get("schema"))
    chart_code = state.get("chart_code")
    chart_image = encode_image_b64(state.get("chart_path"))
    
    # define evaluator LLM-as-judge to refine generated chart
    evaluator = evaluator_llm.with_structured_output(EvaluationCriteria)
    
    # load saved prompt
    prompt = load_prompt("prompts/evaluator_prompt.json")

    # in case of error during last chart generation
    rubric_list = state.get("rubric")
    error = state.get("rubric")[-1]["error"] if rubric_list else None
    if error:
        return {"rubric": rubric_list}
    else:
        # define runnable to invoke with inputs
        chain = RunnableSequence(prompt,evaluator)
        response =  chain.invoke({
                                "user_query":user_query,
                                "schema":schema,
                                "code_v1":chart_code #,
                                #"chart_image":chart_image
                                })
        rubric_list = serialize_rubric(response,state)
        return {"rubric": rubric_list}
    
def check_condition(state:AnalystState) -> Literal["retry","end"]:
    """Check condition for feedback loop"""
    max_retry = state.get("max_retry")
    # calculate total passing evaluation criteria based on objective rubric
    serialized_rubric = state.get("rubric")[-1]
    current_rubric = EvaluationCriteria.model_validate(serialized_rubric)

    rubric_total = current_rubric.has_clarity + current_rubric.has_axis_labels + current_rubric.has_clear_title + current_rubric.has_legend_if_needed + current_rubric.relevance + current_rubric.appropriate_chart_type + current_rubric.correct_data_mapping

    # retry the chart generation if all criteria not fulfilled by prev code or code has error
    if current_rubric.error or (max_retry > 0 and rubric_total < 7):
        return "retry"
    else:
        return "end" 

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
#------------------------------------------Graph creation and invocation-------------------------------#
def create_agent():
    # create a stategraph with Schema 
    graph = StateGraph(AnalystState)
    # add nodes
    graph.add_node("generate_chart_code",generate_chart_code)
    graph.add_node("generate_chart",generate_chart)
    graph.add_node("evaluate_chart",evaluate_chart)
    # add edges
    graph.add_edge(START,"generate_chart_code")
    graph.add_edge("generate_chart_code","generate_chart")
    graph.add_edge("generate_chart","evaluate_chart")
    graph.add_conditional_edges("evaluate_chart",check_condition,{"retry":"generate_chart_code","end":END})

    # compile the graph into a agent
    agent = graph.compile()

    return agent

@traceable(name="run_workflow",tags=["agent","final_state"])
def run_workflow(initial_state:AnalystState) -> AnalystState:
    
    # create reflective agent
    agent = create_agent()

    final_state = agent.invoke(initial_state)
    return final_state

# load the entire csv data into pandas dataframe
# also get the columns with their dtypes as schema of the given data
data_path = "data/titanic.csv"
df,schema = load_csv_data(data_path) 

# define llms for generation and evaluation tasks
generator_llm = ChatOpenAI(model="gpt-4o")
evaluator_llm = ChatOpenAI(model="gpt-4o")

# define initial state -- all required fields
initial_state = {
                "user_query": "Plot the relationship between gender,class and survival rate.",
                 "data": df.head(5).to_dict(orient="records"), # passing sample only
                 "schema": schema, # passing metadata for deeper understanding to the llm
                 "max_retry": 3
                 }
# run the entire workflow
final_state = run_workflow(initial_state)




# enhancements
# 1. create streamlit interface
# 2. expose as endpoints using fastapi
# 3. display initial code and chart, all successive charts and rubric
# 4. catch warnings - done
#
