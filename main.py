from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate,load_prompt
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from langgraph.graph import StateGraph,START,END
from pydantic import BaseModel,Field
from typing import Literal,Annotated,Optional,TypedDict
import pandas as pd
from schema.chart_code_schema import ChartCode
from schema.evaluation_rubric_schema import EvaluationCriteria
from utils import *
from dotenv import load_dotenv

load_dotenv()

# create analyst state schema
class AnalystState(TypedDict):
    user_query : str
    data: dict
    schema: dict
    max_retry: int 
    rubric : Optional[EvaluationCriteria]
    chart: Optional[str]

def generate_chart(state:AnalystState) -> dict:
    """Generate/Revise chart code in python based on user query"""

    # load csv data as str as LLMs can handle textual descriptions of dicts — and load_prompt will accept them.
    user_query = state.get("user_query")
    #data = str(state.get("data"))
    schema = str(state.get("schema"))
    feedback = state["rubric"].feedback if state.get("rubric") else "No feedback yet. This is the first attempt."
    
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
    
    # update max_retry
    state["max_retry"] -= 1
    
    return {"chart":chart_code.code}

def evaluate_chart(state:AnalystState):
    """Evaluate llm-generated chart code and generate appropriate rubric-aligned feedback"""

    user_query = state.get("user_query")
    data = str(state.get("data"))
    schema = str(state.get("schema"))
    chart = state.get("chart")

    # define evaluator LLM-as-judge to refine generated chart
    evaluator = evaluator_llm.with_structured_output(EvaluationCriteria)
    
    # load saved prompt
    prompt = load_prompt("prompts/evaluator_prompt.json")

    # define runnable to invoke with inputs
    chain = RunnableSequence(prompt,evaluator)

    response =  chain.invoke({
                            "user_query":user_query,
                            "schema":schema,
                            "code_v1":chart 
                            })
    
    return {"rubric":response}
    
def check_condition(state:AnalystState) -> Literal["retry","end"]:
    """Check condition for feedback loop"""

    max_retry = state.get("max_retry")
    # calculate total passing evaluation criteria based on objective rubric
    rubric_total = state["rubric"].relevance + state["rubric"].appropriate_chart_type + state["rubric"].correct_data_mapping

    # retry the chart generation if all criteria not fulfilled by prev code
    if max_retry > 0 and rubric_total < 3:
        return "retry"
    else:
        return "end" 
 
#------------------------------------------Graph creation and invocation-------------------------------#
# create a stategraph with Schema 
graph = StateGraph(AnalystState)
# add nodes
graph.add_node("generate_chart",generate_chart)
graph.add_node("evaluate_chart",evaluate_chart)
# add edges
graph.add_edge(START,"generate_chart")
graph.add_edge("generate_chart","evaluate_chart")
graph.add_conditional_edges("evaluate_chart",check_condition,{"retry":"generate_chart","end":END})

# compile the graph into a agent
agent = graph.compile()

# define llms for generation and evaluation tasks
generator_llm = ChatOpenAI(model="gpt-4o-mini")
evaluator_llm = ChatOpenAI(model="gpt-4o")

# load the entire csv data into pandas dataframe
# also get the columns with their dtypes as schema of the given data
df,schema = load_csv_data("data/titanic.csv") 

# define initial state -- all required fields
initial_state = {
                "user_query": "Draw a chart for Survival rate by Passenger class",
                 "data": df.head(5).to_dict(orient="records"), # passing sample only
                 "schema": schema, # passing metadata for deeper understanding to the llm
                 "max_retry": 2
                 }
# invoke the agent
final_state = agent.invoke(initial_state)

# Get the code within the <execute_python> tags
chart_code = extract_python_code(final_state["chart"])
# If code runs successfully, the file chart_v2.png should have been generated
exec_globals = {"df":df}
exec(chart_code,exec_globals)








