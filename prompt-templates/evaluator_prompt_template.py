from langchain_core.prompts import PromptTemplate

template = """
    You are an expert data visualization evaluator.\n
    Your goal is to judge whether a given Python matplotlib/seaborn chart generation code correctly and appropriately fulfills a user’s query.\n\
    You will receive:\n
    - The user query describing the intended visualization.\n
    - The dataset schema (column names and data types).\n
    - The chart generation code.\n\n
    Evaluate the chart on the following True/False criteria:\n
    1. **relevance** — Does this chart accurately address the user’s query intent?\n
    2. **correct_data_mapping** — Are the axes and data encodings mapped correctly based on the dataset schema?\n
    3. **appropriate_chart_type** — Is the chosen chart type suitable for representing the data requested in the query?\n\n
    Then, provide a short feedback paragraph explaining your reasoning or any mistakes you notice.\n\n
    Return your response as a JSON object.

    chart generation code (for context):
    {code_v1}

    user query:
    {user_query}

    dataset schema (columns available in df):
    {schema}
    """

prompt = PromptTemplate(template=template,
                        input_variables=["code_v1","user_query","schema"])

prompt.save("prompts/evaluator_prompt.json")
