# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend and frontend folders into the container
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port 8000 for FastAPI
EXPOSE 8000

# Move into the backend directory and run the application
WORKDIR /app/backend
CMD ["python", "main.py"]
