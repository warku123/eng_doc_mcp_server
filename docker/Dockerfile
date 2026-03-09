FROM python:3.11-slim

WORKDIR /app

# Install curl for downloading index
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py .

# Create docs directory and download index during build
RUN mkdir -p site/search && \
    curl -L -o site/search/search_index.json \
    https://raw.githubusercontent.com/tronprotocol/documentation-en/gh-pages/search/search_index.json && \
    echo "Index downloaded successfully"

# Expose port
EXPOSE 8001

# Start server
CMD ["python", "mcp_server.py"]
