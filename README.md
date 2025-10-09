# AtmoSwing web API to serve the forecasts

[![Tests](https://github.com/atmoswing/atmoswing-api/actions/workflows/tests.yml/badge.svg)](https://github.com/atmoswing/atmoswing-api/actions/workflows/tests.yml)
[![GitHub release](https://img.shields.io/github/v/release/atmoswing/atmoswing-api?color=blue)](https://github.com/atmoswing/atmoswing-api)
[![Docker Image Version](https://img.shields.io/docker/v/atmoswing/web-api?color=blue)](https://hub.docker.com/r/atmoswing/web-api)
[![PyPI](https://img.shields.io/pypi/v/atmoswing-api?color=blue)](https://pypi.org/project/atmoswing-api/)
![Static Badge](https://img.shields.io/badge/python-%3E%3D3.10-blue)

## Setup

Specify the environment variables in a `.env` file:

```dotenv
# .env
# Directory where the forecasts are stored
data_dir=/opt/atmoswing/data
```

## Usage with Docker

The easiest way to use the AtmoSwing API is through Docker (Image available on Docker Hub). Here is an example of a docker-compose.yml file:

```yml
version: "3.8"

services:
  atmoswing-api:
    image: atmoswing/atmoswing-api:main
    container_name: atmoswing-api-main
    ports:
      - "8000:8000"
    volumes:
      - /home/ubuntu/data:/app/data
      - /home/atmoswing_adn/home:/app/data/adn
      - /home/atmoswing_zap/home:/app/data/zap
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    restart: unless-stopped

  redis:
    image: redis:7
    container_name: atmoswing-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
```

## Cleanup

To remove the past forecasts automatically, set a cron tab to run:

```
sudo docker exec atmoswing-api-main python3 /app/atmoswing_api/app/utils/cleaner.py --data-dir /app/data --keep-days 60
```


## Development

Run the local server from the IDE with: 

    uvicorn app.main:app --reload

## Documentation

The API documentation is available at:
- [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI
- [http://localhost:8000/redoc](http://localhost:8000/redoc) for the ReDoc UI
- [http://localhost:8000/minidocs](http://localhost:8000/minidocs) customized minimal documentation
- [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) for the OpenAPI JSON schema
