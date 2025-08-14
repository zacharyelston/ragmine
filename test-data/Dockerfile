FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test data and scripts
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Default command loads all test data
CMD ["python", "load_test_data.py"]
