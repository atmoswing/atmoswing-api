import pytest
import asyncio
from atmoswing_api.app.services.general import *

@pytest.fixture
def mock_data_dir(tmp_path):
    """Fixture to create a temporary data directory with mock regions and files."""
    region_dir = tmp_path / "region1" / "2024" / "10" / "15"
    region_dir.mkdir(parents=True)
    (region_dir / "2024-10-15_12.method.entity.nc").touch()
    return str(tmp_path)

@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files(mock_data_dir):
    region = "region1"
    result = await get_last_forecast_date_from_files(mock_data_dir, region)
    assert result["last_forecast_date"] == "2024-10-15T12"
