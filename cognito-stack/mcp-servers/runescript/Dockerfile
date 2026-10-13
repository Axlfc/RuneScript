FROM python:3.11-slim

WORKDIR /app/mcp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/mcp
ENV RUNESCRIPT_PATH=/app

ENTRYPOINT ["python3", "-m", "src.server"]
