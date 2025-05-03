# Use official Python image
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your code
COPY . .

# Expose the port your Flask app runs on
EXPOSE 10000

# Start the Flask app
CMD ["python", "app.py"]
