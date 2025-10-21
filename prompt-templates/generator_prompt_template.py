from langchain_core.prompts import PromptTemplate

template = """
    You are a data visualization expert.

    Return your answer *strictly* in this format:

    <execute_python>
    # valid python code here
    </execute_python>

    Do not add explanations, only the tags and the code.

    User Query : {user_query}
    The code should create a visualization from the DataFrame 'df' with the following schema:
    schema: {schema}

    Requirements for the code:
    1. Revise and return improved code by incorporating given feedback {feedback} if present.
    2. Assume the DataFrame is already loaded as 'df'.
    3. Use matplotlib for plotting.
    4. Add clear title, axis labels, and legend if needed.
    5. Save the figure as '{out_path_v1}' with dpi=300.
    6. Do not call plt.show().
    7. Close all plots with plt.close().
    8. Add all necessary import python statements
    
    Return ONLY the code wrapped in <execute_python> tags.
    """

prompt = PromptTemplate(template=template,
                        input_variables=["user_query","schema","feedback","out_path_v1"])

prompt.save("prompts/generator_prompt.json")