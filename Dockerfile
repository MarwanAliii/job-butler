# Use official Python image
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Unbuffer stdout so print() shows up in logs immediately
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install --with-deps

# Copy your code
COPY . .

# Expose the port your Flask app runs on
EXPOSE 10000

# Start the Flask app
CMD ["python", "app.py"]
