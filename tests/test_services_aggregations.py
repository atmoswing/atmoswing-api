import pytest
from datetime import datetime

from atmoswing_api.app.services.aggregations import *

# Path to the data directory
cwd = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(cwd, "data")


@pytest.mark.asyncio
async def test_get_entities_analog_values_percentile():
    # /aggregations/adn/2024-10-05T00/4Zo-CEP/2024-10-07T00/analog-values-percentile/60
    result = await get_entities_analog_values_percentile(
        data_dir, region="adn", forecast_date="2024-10-05", method="4Zo-CEP",
        lead_time="2024-10-07", percentile=90)

    assert result["entity_ids"] == [1,2,3,4,5,6,7,8,9]
    assert result["values"] == pytest.approx(
        [18.47,18.14,67.0,25.25,17.77,24.74,28.81,29.31,23.91], rel=1e-2)


@pytest.mark.asyncio
async def test_get_series_synthesis_per_method():
    # /aggregations/adn/2024-10-05T00/series-synthesis-per-method/90
    result = await get_series_synthesis_per_method(
        data_dir, region="adn", forecast_date="2024-10-05", percentile=90)

    assert len(result) == 6

    # Extract the list of methods
    methods = [item["method_id"] for item in result]
    assert "4Zo-GFS" in methods
    assert "4Zo-ARPEGE" in methods
    assert "4Zo-CEP" in methods
    assert "2Z-2MI-24h-GFS" in methods
    assert "2Z-06h-CEP" in methods
    assert "2Z-06h-GFS" in methods

    # Look for the 4Zo-GFS method in the results (list)
    idx_4Zo_GFS = next(
        (i for i, item in enumerate(result) if item["method_id"] == "4Zo-GFS"),
        None
    )
    assert result[idx_4Zo_GFS]["target_dates"] == [
        datetime(2024, 10, 5),
        datetime(2024, 10, 6),
        datetime(2024, 10, 7),
        datetime(2024, 10, 8),
        datetime(2024, 10, 9),
        datetime(2024, 10, 10),
        datetime(2024, 10, 11),
        datetime(2024, 10, 12)
    ]
    assert result[idx_4Zo_GFS]["values"] == pytest.approx(
        [0.60, 21.72, 60.28, 61.00, 61.05, 27.99, 14.10, 24.25], rel=1e-2)


@pytest.mark.asyncio
async def test_get_series_synthesis_total():
    # /aggregations/adn/2024-10-05T00/series-synthesis-total/90
    result = await get_series_synthesis_total(
        data_dir, region="adn", forecast_date="2024-10-05", percentile=90)

    assert len(result) == 2
    assert result[0]["time_step"] == 6
    assert result[1]["time_step"] == 24
    assert result[1]["values"][1] == pytest.approx(34.8, rel=1e-2)
    assert result[1]["values"][2] == pytest.approx(92.06, rel=1e-2)
    assert result[1]["values"][3] == pytest.approx(61, rel=1e-2)
