# Use a Python image compatible with ARM architecture (Raspberry Pi)
FROM arm64v8/python:3.9-slim-bullseye

# Install dependencies including Chromium and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium \
    chromium-driver \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation

# Copy the requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app /app

# Set environment variables for the ChromeDriver path, input CSV, and output CSV
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver
ENV INPUT_CSV_PATH=/input/occupation_input.csv
ENV OUTPUT_CSV_PATH=/output/occupation_credentials_output.csv

# Set the working directory
WORKDIR /app

# Entry point for the Docker container
CMD ["python", "main.py"]
