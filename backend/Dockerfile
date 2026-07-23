# FROM python:3.12-slim

# # Set working directory
# WORKDIR /app

# # Copy requirements first (better caching)
# COPY requirements.txt .

# # Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application code
# COPY backend/app ./app          
# COPY database ./database 

# # Expose port
# EXPOSE 8000

# # Run FastAPI
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app          

EXPOSE 8000

CMD python app/services/ingestion.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT