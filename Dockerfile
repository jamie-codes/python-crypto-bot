# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose metrics port
EXPOSE 8000

# Run the bot
CMD ["python", "crypto-arbitrage.py"]
