FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv pip install --system google-genai cryptography fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg httpx pydantic python-dotenv web3
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
