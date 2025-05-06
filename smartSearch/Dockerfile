FROM python:3.10-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements first (for layer caching)
WORKDIR /app
COPY requirements.txt .

# 3. Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . .

# 5. Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]