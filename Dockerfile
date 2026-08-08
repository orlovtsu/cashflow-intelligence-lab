FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY cashflow ./cashflow
COPY scripts ./scripts
EXPOSE 8000
CMD ["uvicorn", "cashflow.api:app", "--host", "0.0.0.0", "--port", "8000"]
