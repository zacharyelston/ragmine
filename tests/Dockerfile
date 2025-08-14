FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Make test scripts executable
RUN chmod +x scripts/*.sh

# Default command runs all tests
CMD ["pytest", "tests/", "-v", "--tb=short"]
