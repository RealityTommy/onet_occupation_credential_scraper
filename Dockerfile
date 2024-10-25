# Use the official Python 3 image compatible with ARM architecture
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies for Selenium and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium-browser \
    chromium-driver \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY app /app/app
COPY .env /app/.env

# Set environment variables for Chrome and ChromeDriver paths
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver
ENV INPUT_CSV_PATH=/app/input/occupation_input.csv
ENV OUTPUT_CSV_PATH=/app/output/occupation_credentials_output.csv

# Expose any necessary ports (if applicable)
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
