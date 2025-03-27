import pytest
from datetime import datetime

from atmoswing_api.app.services.aggregations import *


@pytest.mark.asyncio
async def test_get_entities_analog_values_percentile():
    # /aggregations/adn/2024-10-05T00/4Zo-CEP/2024-10-07T00/analog-values-percentile/60
    result = await get_entities_analog_values_percentile(
        "./data", region="adn", forecast_date="2024-10-05", method="4Zo-CEP",
        target_date="2024-10-07", percentile=90)

    assert result["entity_ids"] == [1,2,3,4,5,6,7,8,9]
    assert result["values"] == pytest.approx(
        [18.47,18.14,67.0,25.25,17.77,24.74,28.81,29.31,23.91], rel=1e-2)
