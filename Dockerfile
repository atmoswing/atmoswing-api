# atmoswing/atmoswing-api

FROM python:3.12-slim

# Set environment variables for Python behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install weasyprint
RUN apt-get update && \
    apt-get install -y weasyprint

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the package and install it
COPY . .
RUN pip install --no-cache-dir .

# Expose port for FastAPI
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "atmoswing_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
