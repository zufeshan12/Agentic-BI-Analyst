# -------- Backend Dockerfile (FastAPI) --------
FROM ghcr.io/astral-sh/uv:python3.10-bookworm

# Set working directory
WORKDIR /app

# Copy project dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy backend source files
COPY ./backend /app/backend

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
