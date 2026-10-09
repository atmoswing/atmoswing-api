# atmoswing/web-api

FROM python:3.12-slim

# Set environment variables for Python behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Copy the package and install it with its dependencies
COPY pyproject.toml README.md LICENSE ./
COPY atmoswing_api ./atmoswing_api
RUN pip install --no-cache-dir .

# Expose port for FastAPI
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "atmoswing_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
