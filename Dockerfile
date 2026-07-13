FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Create tables before starting
CMD python -c "from database import init_db; init_db()" && python seed.py && streamlit run app.py --server.address=0.0.0.0