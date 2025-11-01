# -------- Frontend Dockerfile (Streamlit) --------
FROM ghcr.io/astral-sh/uv:python3.10-bookworm

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

RUN uv add streamlit
RUN uv sync --frozen --no-dev

# Copy Streamlit app files
COPY ./frontend /app/frontend

# Expose Streamlit port
EXPOSE 8501

# Launch Streamlit
CMD ["uv", "run", "streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
