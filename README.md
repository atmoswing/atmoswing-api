# AtmoSwing web API to serve the forecasts

[![Tests](https://github.com/atmoswing/atmoswing-api/actions/workflows/tests.yml/badge.svg)](https://github.com/atmoswing/atmoswing-api/actions/workflows/tests.yml)
[![GitHub release](https://img.shields.io/github/v/release/atmoswing/atmoswing-api?color=blue)](https://github.com/atmoswing/atmoswing-api)
[![PyPI](https://img.shields.io/pypi/v/atmoswing-api?color=blue)](https://pypi.org/project/atmoswing-api/)
![Static Badge](https://img.shields.io/badge/python-%3E%3D3.10-blue)

## Development

Run the local server from the IDE with: 

    uvicorn app.main:app --reload

## Setup

Specify the environment variables in a `.env` file:

```dotenv
# .env
# Directory where the forecasts are stored
data_dir=/opt/atmoswing/data
```