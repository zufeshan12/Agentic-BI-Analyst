import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image
from utils import clear_charts


FASTAPI_URL = "http://localhost:8000/analyze"
CHARTS_URL = "http://localhost:8000/"

st.set_page_config(page_title="Agentic BI Analyst", layout="wide")
st.title("📊 Agentic BI Analyst Demo")

# --- Sidebar / Controls ---
st.sidebar.header("⚙️ Controls")
clear = st.sidebar.button("🧹 Clear Output")

if clear:
    st.session_state.clear()
    
# --- Upload + Inputs ---
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
user_query = st.text_area("Describe the visualization you want:", height=50)
max_retry = st.number_input("Max retries", min_value=1, max_value=5, value=3)

if st.button("Generate Charts"):
    # clear the Charts folder
    clear_charts()

    if uploaded_file and user_query.strip():
        files = {"file": uploaded_file.getvalue()}
        data = {"user_query": user_query, "max_retry": str(max_retry)}

        with st.spinner("⏳ Running your agentic workflow..."):
            response = requests.post(FASTAPI_URL, files=files, data=data)

        if response.status_code == 200:
            result = response.json()['response']
            charts = result.get("charts", [])
            rubrics = result.get("rubric_feedback", [])

            if not charts:
                st.error("No charts were generated.")
            else:
                st.success(f"✅ Generated {len(charts)} chart versions")

                for i, (chart_path, rubric) in enumerate(zip(charts, rubrics)):
                    st.markdown(f"### 🧩 Iteration {i+1}")
                    cols = st.columns([2, 3])

                    # --- Display Chart ---
                    with cols[0]:
                        chart_url = f"{CHARTS_URL}/{chart_path}"
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
