import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image
import os


BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
CLEAR_CHARTS_URL = f"{BACKEND_URL}/charts/delete"

def clear_charts():
    """Hit delete api endpoint to delete existing charts"""
    try:
        response = requests.delete(CLEAR_CHARTS_URL)
        if response.status_code == 200:
            st.success("Existing charts cleared successfully.")
        else:
            st.error("Failed to clear existing charts")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")

st.set_page_config(page_title="Agentic BI Analyst", layout="wide")
st.title("📊 Agentic BI Analyst Demo")

# --- Sidebar / Controls ---
st.sidebar.header("Controls")
clear = st.sidebar.button("Clear Output",width = "stretch",type="secondary")

# Initialize session state for storing recent queries
if "recent_queries" not in st.session_state:
    st.session_state["recent_queries"] = []

# Sidebar — display last 5 queries
st.sidebar.header("Recent Queries")
if st.session_state["recent_queries"]:
    for i, q in enumerate(reversed(st.session_state["recent_queries"]), 1):
        st.sidebar.markdown(f"**{i}.** {q}")
else:
    st.sidebar.info("No recent queries yet.")

if clear:
    st.session_state.clear()
    
# --- Upload + Inputs ---
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
user_query = st.text_area("Describe the visualization you want:", height=50)
max_retry = st.number_input("Max retries", min_value=1, max_value=5, value=3)

if st.button("Generate Charts",width="stretch",type="primary"):
    # clear the Charts folder
    clear_charts()
    
    # check for required inputs from user
    if uploaded_file and user_query.strip():
        files = {"file": uploaded_file.getvalue()}
        data = {"user_query": user_query, "max_retry": str(max_retry)}

        with st.spinner("⏳ Running your agentic workflow..."):
            FASTAPI_URL = f"{BACKEND_URL}/analyze"
            response = requests.post(FASTAPI_URL, files=files, data=data)

        if response.status_code == 200:
            result = response.json()['response']
            charts = result.get("charts", [])
            rubrics = result.get("rubric_feedback", [])

            # append user query to the session state
            st.session_state["recent_queries"].append(user_query)
            st.session_state["recent_queries"] = st.session_state["recent_queries"][-5:]

            if not charts:
                st.error("No charts were generated.")
            else:
                st.success(f"✅ Generated {len(charts)} chart versions")

                for i, (chart_path, rubric) in enumerate(zip(charts, rubrics)):
                    st.markdown(f"### 🧩 Iteration {i+1}")
                    cols = st.columns([2, 3])

                    # --- Display Chart ---
                    with cols[0]:
                        chart_url = f"{BACKEND_URL}/{chart_path}"
                        img_response = requests.get(chart_url)
                        if img_response.status_code == 200:
                            image = Image.open(BytesIO(img_response.content))
                            st.image(image, caption=chart_path, use_container_width=True)
                        else:
                            st.warning(f"Chart not found at: {chart_url}")

                    # --- Display Rubric ---
                    with cols[1]:
                        st.markdown("**Rubric Feedback**")
                        if rubric:
                            df = pd.DataFrame(list(rubric.items()), columns=["Criteria", "Score"])
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No rubric feedback available for this iteration.")
        else:
            st.error(f"❌ Request failed: {response.text}")
    else:
        st.warning("Please upload a CSV and enter a valid query.")

# Footer / Citation
st.markdown(
    """
    <hr style="margin-top: 200px; margin-bottom: 10px; border: 1px solid gray;">
    <p style='text-align: center; color: gray; font-size: 1.0em;'>
        Crafted with ❤️ by Zufeshan Imran · © 2025
    </p>
    """,
    unsafe_allow_html=True
)
