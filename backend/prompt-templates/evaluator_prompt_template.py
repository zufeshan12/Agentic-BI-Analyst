from langchain_core.prompts import PromptTemplate

template = """
    You are an expert data visualization evaluator.\n
    Your task: Critique given IMAGE and original code for correctness based on user query.\n\
    You will receive:\n
    - The user query describing the intended visualization.\n
    - The dataset schema (column names and data types).\n
    - The chart generation code.\n\n
    - The generated chart 
    Evaluate the chart on the following True/False criteria:\n
    1. **relevance** — Does this chart accurately address the user’s query intent?\n
    2. **correct_data_mapping** — Are the axes and data encodings mapped correctly based on the dataset schema?\n
    3. **appropriate_chart_type** — Is the chosen chart type suitable for representing the data requested in the query?\n
    4. **has_clear_title** - Does this chart have clear title?\n
    5. **has_axis_labels** - 
    6. **has_legend_if_needed** - 
    7. **has_clarity** - 
    Then, provide a short feedback paragraph explaining your reasoning or any mistakes you notice.\n\n
    Return your response as a JSON object.

    chart generation code (for context):
    {code_v1}

    chart image:
    {chart_image}

    user query:
    {user_query}

    dataset schema (columns available in df):
    {schema}
    """

prompt = PromptTemplate(template=template,
                        input_variables=["code_v1","chart_image","user_query","schema"])

prompt.save("backend/prompts/evaluator_prompt.json")
