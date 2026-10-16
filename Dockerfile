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

# Run the API as a non-root user. It only reads the data directory: at run time,
# give it read access to the region directories with `group_add` (docker compose),
# or change its UID/GID with `user`. The cron jobs writing to the data directory
# (cleaner, warmup) are run as root with `docker exec -u 0`.
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid ${APP_GID} atmoswing \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --no-create-home \
       --shell /usr/sbin/nologin atmoswing
USER atmoswing

# Expose port for FastAPI
EXPOSE 8000

# Python is used as curl is not available in the slim image
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

# Command to run the application. Behind a reverse proxy, set FORWARDED_ALLOW_IPS so
# that the client addresses are taken from X-Forwarded-For. The number of worker
# processes can be set with WEB_CONCURRENCY (default: 1).
CMD ["uvicorn", "atmoswing_api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
