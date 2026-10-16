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
# Optional: file receiving the errors (all messages when debug=true).
# Logs always go to the terminal (stdout in Docker).
log_file=/var/log/atmoswing-api/app.log
# Optional: verbose logging of the API (not of third-party libraries)
debug=false
# Optional: requests allowed per client IP, all routes together (default: 600/minute)
rate_limit=600/minute
```

## Usage with Docker

The easiest way to use the AtmoSwing API is through Docker (Image available on Docker Hub). Here is an example of a docker-compose.yml file:

```yml
version: "3.8"

services:
  atmoswing-api:
    image: atmoswing/atmoswing-api:main
    container_name: atmoswing-api-main
    # The API runs as a non-root user (UID/GID 1000 by default) and only reads the
    # data. Add the groups owning the region directories (numeric GIDs, see
    # `getent group atmoswing_adn`), or set `user: "<uid>:<gid>"`.
    group_add:
      - "1001"  # atmoswing_adn
      - "1002"  # atmoswing_zap
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
      # Address(es) of the reverse proxy, trusted to report the client IP through
      # X-Forwarded-For (comma-separated IPs or networks). Without it, all clients
      # behind the proxy share the same rate limit budget.
      - FORWARDED_ALLOW_IPS=172.16.0.0/12
    restart: unless-stopped

  redis:
    image: redis:7
    container_name: atmoswing-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
```

Rate limiting identifies clients by their IP address. When the API runs behind a
reverse proxy (nginx, Traefik, ...), set `FORWARDED_ALLOW_IPS` to the address the
proxy connects from (e.g. its Docker network), and make the proxy set the
`X-Forwarded-For` header. Never use `*` when the API port is reachable without the
proxy: clients could then send any address and bypass the rate limit.

The forecast files must be readable by the groups added with `group_add` (e.g.
uploaded with an SFTP umask of 027 or 022). To check the access of the API user:

```
sudo docker exec atmoswing-api-main ls /app/data/adn
```

The image has a health check (`/health`, not rate limited); `docker ps` shows the
container status. Set `WEB_CONCURRENCY` to run several worker processes (each one
has its own rate limit counters).

## Scheduled jobs

The scripts writing to the data directory run as root (`-u 0`), since the API user
only has read access. To remove the past forecasts and precompute the heavy
requests, set a cron tab such as:

```
# Remove the forecasts older than 60 days (daily at 02:00)
0 2 * * * sudo docker exec -u 0 atmoswing-api-main python3 /app/atmoswing_api/scripts/cleaner.py --data-dir /app/data --keep-days 60
# Precompute the heavy requests of the last 10 days (every 10 minutes)
*/10 * * * * sudo docker exec -u 0 atmoswing-api-main python3 /app/atmoswing_api/scripts/warmup_cache.py --data-dir /app/data --days 10
```


## Development

Run the local server from the IDE with: 

    uvicorn atmoswing_api.app.main:app --reload

## Documentation

The API documentation is available at:
- [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI
- [http://localhost:8000/redoc](http://localhost:8000/redoc) for the ReDoc UI
- [http://localhost:8000/minidocs](http://localhost:8000/minidocs) customized minimal documentation
- [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) for the OpenAPI JSON schema
