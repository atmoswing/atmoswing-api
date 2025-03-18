from unittest import result

import pytest
from datetime import datetime

from atmoswing_api.app.services.forecasts import get_analog_values, get_analog_dates, \
    get_analog_criteria, get_analogs, get_series_analog_values_best


@pytest.mark.asyncio
async def test_get_analog_values():
    # /forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/2024-10-07/values
    result = await get_analog_values("./data", region="adn", forecast_date="2024-10-05",
                                     method="4Zo-CEP", configuration="Alpes_Nord",
                                     entity=3, target_date="2024-10-07")
    result = result["values"]

    assert result == pytest.approx([0.5, 2.9, 59.6, 0.0, 23.8, 1.3, 83.1, 64.2, 9.3,
                                    37.1, 6.2, 0.2, 6.3, 2.1, 31.9, 25.4, 0.0, 16.3,
                                    39.1, 40.7, 8.0, 103.0, 12.0, 0.8])


@pytest.mark.asyncio
async def test_get_analog_dates():
    # /forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/dates
    result = await get_analog_dates("./data", region="adn", forecast_date="2024-10-05",
                                    method="4Zo-CEP", configuration="Alpes_Nord",
                                    target_date="2024-10-07")
    result = result["dates"]

    assert result == [datetime(1993, 10, 11),
                      datetime(1995, 11, 10),
                      datetime(1993, 10, 5),
                      datetime(2006, 11, 24),
                      datetime(1960, 11, 21),
                      datetime(2000, 11, 12),
                      datetime(2006, 10, 23),
                      datetime(1970, 11, 18),
                      datetime(1993, 9, 7),
                      datetime(1960, 10, 22),
                      datetime(1977, 10, 5),
                      datetime(2010, 10, 3),
                      datetime(1968, 10, 31),
                      datetime(1982, 9, 25),
                      datetime(2002, 10, 21),
                      datetime(1976, 10, 11),
                      datetime(2012, 10, 17),
                      datetime(1996, 11, 10),
                      datetime(1963, 11, 25),
                      datetime(2004, 10, 28),
                      datetime(1976, 11, 9),
                      datetime(1958, 9, 30),
                      datetime(1998, 9, 26),
                      datetime(1970, 10, 6)]


@pytest.mark.asyncio
async def test_get_analog_criteria():
    # /forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/dates
    result = await get_analog_criteria(
        "./data", region="adn", forecast_date="2024-10-05", method="4Zo-CEP",
        configuration="Alpes_Nord", target_date="2024-10-07")
    result = result["criteria"]

    assert result == pytest.approx(
        [37.792, 37.9767, 37.9801, 39.0845, 40.6235, 40.7622, 41.6019, 41.9558, 42.1433,
         42.372, 42.4879, 42.8375, 42.8489, 43.0062, 43.1032, 43.1961, 43.4443, 43.5633,
         43.5815, 43.6208, 43.6322, 43.8155, 43.9426, 44.2276], rel=1e-3)


@pytest.mark.asyncio
async def test_get_analogs():
    # /forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/2024-10-07/analogs
    result = await get_analogs("./data", region="adn", forecast_date="2024-10-05",
                               method="4Zo-CEP", configuration="Alpes_Nord",
                               entity=3, target_date="2024-10-07")
    result = result["analogs"]

    assert result[0]["date"] == datetime(1993, 10, 11)
    assert result[0]["value"] == pytest.approx(0.5)
    assert result[0]["criteria"] == pytest.approx(37.792, rel=1e-3)
    assert result[0]["rank"] == 1

    assert result[1]["date"] == datetime(1995, 11, 10)
    assert result[1]["value"] == pytest.approx(2.9)
    assert result[1]["criteria"] == pytest.approx(37.977, rel=1e-3)
    assert result[1]["rank"] == 2

    assert result[9]["date"] == datetime(1960, 10, 22)
    assert result[9]["value"] == pytest.approx(37.1)
    assert result[9]["criteria"] == pytest.approx(42.372, rel=1e-3)
    assert result[9]["rank"] == 10

    assert result[23]["date"] == datetime(1970, 10, 6)
    assert result[23]["value"] == pytest.approx(0.8)
    assert result[23]["criteria"] == pytest.approx(44.228, rel=1e-3)
    assert result[23]["rank"] == 24


@pytest.mark.asyncio
async def get_series_analog_values_10_best():
    # /forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/series-values-best-analogs
    result = await get_series_analog_values_best(
        "./data", region="adn", forecast_date="2024-10-05", method="4Zo-CEP",
        configuration="Alpes_Nord", entity=3, number=10)

    result = result["series_values"]

    assert result[0] == pytest.approx(
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], rel=1e-2)
    assert result[1] == pytest.approx(
        [20.5, 1.8, 1.6, 0, 5.1, 3.3, 4.9, 8, 1.8, 0], rel=1e-2)
    assert result[2] == pytest.approx(
        [0.5, 2.9, 59.6, 0, 23.8, 1.3, 83.1, 64.2, 9.3, 37.1], rel=1e-2)
    assert result[7] == pytest.approx(
        [2.4, 1.6, 13.3, 0, 0, 16.2, 0, 0, 0.1, 0.5], rel=1e-2)


@pytest.mark.asyncio
async def get_series_analog_values_5_best():
    # /forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/series-values-best-analogs?number=5
    result = await get_series_analog_values_best(
        "./data", region="adn", forecast_date="2024-10-05", method="4Zo-CEP",
        configuration="Alpes_Nord", entity=3, number=5)

    result = result["series_values"]

    assert result[0] == pytest.approx(
        [0, 0, 0, 0, 0], rel=1e-2)
    assert result[1] == pytest.approx(
        [20.5, 1.8, 1.6, 0, 5.1], rel=1e-2)
    assert result[2] == pytest.approx(
        [0.5, 2.9, 59.6, 0, 23.8], rel=1e-2)
    assert result[7] == pytest.approx(
        [2.4, 1.6, 13.3, 0, 0], rel=1e-2)
