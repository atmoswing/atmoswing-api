import pytest
import asyncio
from atmoswing_api.app.services.general import *

@pytest.fixture
def mock_data_dir(tmp_path):
    """Fixture to create a temporary data directory with mock regions and files."""
    region_dir = tmp_path / "region1" / "2024" / "10" / "15"
    region_dir.mkdir(parents=True)
    (region_dir / "2024-10-15_00.method.entity.nc").touch()
    (region_dir / "2024-10-15_06.method.entity.nc").touch()
    (region_dir / "2024-10-15_12.method.entity.nc").touch()
    return str(tmp_path)

@pytest.fixture
def mock_data_dir_no_files(tmp_path):
    """Fixture to create a temporary data directory with mock regions but no files."""
    region_dir = tmp_path / "region1" / "2024" / "10" / "15"
    region_dir.mkdir(parents=True)
    return str(tmp_path)

@pytest.fixture
def mock_data_dir_bad_subdir(tmp_path):
    """Fixture to create a temporary data directory with mock regions but no files."""
    region_dir = tmp_path / "region1" / "2024" / "AA" / "BB"
    region_dir.mkdir(parents=True)
    return str(tmp_path)

@pytest.fixture
def mock_data_dir_no_subdir(tmp_path):
    """Fixture to create a temporary data directory with no subdirectories."""
    region_dir = tmp_path / "region1"
    region_dir.mkdir(parents=True)
    return str(tmp_path)

# Test get_last_forecast_date_from_files
@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files(mock_data_dir):
    region = "region1"
    result = await get_last_forecast_date_from_files(mock_data_dir, region)
    assert result["last_forecast_date"] == "2024-10-15T12"

# Test get_last_forecast_date_from_files with wrong region
@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files_wrong_region(mock_data_dir):
    region = "region2"
    with pytest.raises(FileNotFoundError):
        await get_last_forecast_date_from_files(mock_data_dir, region)

# Test get_last_forecast_date_from_files with no files
@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files_no_files(mock_data_dir_no_files):
    region = "region1"
    with pytest.raises(ValueError):
        await get_last_forecast_date_from_files(mock_data_dir_no_files, region)

# Test get_last_forecast_date_from_files with bad subdirectories
@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files_bad_subdir(mock_data_dir_bad_subdir):
    region = "region1"
    with pytest.raises(ValueError):
        await get_last_forecast_date_from_files(mock_data_dir_bad_subdir, region)

# Test get_last_forecast_date_from_files with no subdirectories
@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files_no_subdir(mock_data_dir_no_subdir):
    region = "region1"
    with pytest.raises(ValueError):
        await get_last_forecast_date_from_files(mock_data_dir_no_subdir, region)