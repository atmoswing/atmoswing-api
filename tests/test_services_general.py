import pytest
import asyncio
from unittest.mock import patch, MagicMock

from atmoswing_api.app.services.general import get_last_forecast_date_from_files, \
    _get_last_forecast_date, get_method_list, _get_methods_from_netcdf


@pytest.mark.asyncio
@patch("atmoswing_api.app.services.general._get_last_forecast_date")
@patch("atmoswing_api.app.utils.utils.check_region_path")
async def test_get_last_forecast_date_from_files(mock_check_region_path, mock_get_last_forecast_date):
    # Mock check_region_path
    mock_check_region_path.return_value = "/mocked/region/path"

    # Mock _get_last_forecast_date
    mock_get_last_forecast_date.return_value = "2023-01-01T12"

    result = await get_last_forecast_date_from_files("/mocked/data_dir", "region")

    assert result == {"last_forecast_date": "2023-01-01T12"}
    mock_check_region_path.assert_called_once_with("/mocked/data_dir", "region")
    mock_get_last_forecast_date.assert_called_once_with("/mocked/region/path")


@patch("os.listdir")
@patch("atmoswing_api.app.utils.utils.convert_to_datetime")
def test_get_last_forecast_date(mock_convert_to_datetime, mock_listdir):
    # Mock os.listdir for each directory level
    mock_listdir.side_effect = [
        ["2023"],
        ["01"],
        ["01"],
        ["2023-01-01_12.method.region.nc"]
    ]

    # Mock convert_to_datetime to pass the validation
    mock_convert_to_datetime.return_value = None

    region_path = "/mocked/region/path"
    result = _get_last_forecast_date(region_path)

    assert result == "2023-01-01T12"
    mock_listdir.assert_any_call(f"{region_path}")
    mock_listdir.assert_any_call(f"{region_path}/2023")
    mock_listdir.assert_any_call(f"{region_path}/2023/01")
    mock_listdir.assert_any_call(f"{region_path}/2023/01/01")
    mock_convert_to_datetime.assert_called_once_with("2023-01-01T12")


@patch("os.listdir")
def test_get_last_forecast_date_no_subdirs(mock_listdir):
    # Mock os.listdir to return an empty list
    mock_listdir.return_value = []

    with pytest.raises(ValueError, match="No subdirectories found in /mocked/region/path"):
        _get_last_forecast_date("/mocked/region/path")


@patch("os.listdir")
def test_get_last_forecast_date_no_files(mock_listdir):
    # Mock os.listdir for subdirectories and an empty file list
    mock_listdir.side_effect = [
        ["2023"],
        ["01"],
        ["01"],
        []  # No files
    ]

    with pytest.raises(ValueError, match="No files found in /mocked/region/path/2023/01/01"):
        _get_last_forecast_date("/mocked/region/path")


@patch("os.listdir")
def test_get_last_forecast_date_invalid_file_format(mock_listdir):
    # Mock os.listdir for subdirectories and an invalid file format
    mock_listdir.side_effect = [
        ["2023"],
        ["01"],
        ["01"],
        ["invalid.nc"]  # Invalid file format
    ]

    with pytest.raises(ValueError, match="Invalid file format"):
        _get_last_forecast_date("/mocked/region/path")


@patch("os.listdir")
def test_get_last_forecast_date_invalid_datetime_format(mock_listdir):
    # Mock os.listdir for subdirectories and an invalid file format
    mock_listdir.side_effect = [
        ["2023"],
        ["01"],
        ["01"],
        ["invalid_file_name.nc"]  # Invalid file format
    ]

    with pytest.raises(ValueError, match="Invalid datetime format"):
        _get_last_forecast_date("/mocked/region/path")


@pytest.mark.asyncio
@patch("atmoswing_api.app.services.general._get_methods_from_netcdf")
@patch("atmoswing_api.app.utils.utils.check_region_path")
async def test_get_method_list(mock_check_region_path, mock_get_methods):
    # Mock check_region_path
    mock_check_region_path.return_value = "/mocked/region/path"

    # Mock _get_methods_from_netcdf
    mock_get_methods.return_value = [
        {"id": 1, "name": "Method A"},
        {"id": 2, "name": "Method B"},
    ]

    result = await get_method_list("/mocked/data_dir", "region", "2023-01-01")

    assert result == {
        "methods": [{"id": 1, "name": "Method A"}, {"id": 2, "name": "Method B"}]}
    mock_check_region_path.assert_called_once_with("/mocked/data_dir", "region")
    mock_get_methods.assert_called_once_with("/mocked/region/path", "2023-01-01")


@patch("atmoswing_api.app.utils.utils.list_files")
@patch("xarray.open_dataset")
def test_get_methods_from_netcdf(mock_open_dataset, mock_list_files):
    # Mock list_files
    mock_list_files.return_value = ["/mocked/file1.nc", "/mocked/file2.nc"]

    # Mock NetCDF datasets
    mock_ds1 = MagicMock()
    mock_ds1.method_id = 1
    mock_ds1.method_id_display = "Method A"
    mock_ds1.__enter__.return_value = mock_ds1  # For the sorting to work

    mock_ds2 = MagicMock()
    mock_ds2.method_id = 2
    mock_ds2.method_id_display = "Method B"
    mock_ds2.__enter__.return_value = mock_ds2  # For the sorting to work

    mock_open_dataset.side_effect = [mock_ds1, mock_ds2]

    result = _get_methods_from_netcdf("/mocked/region/path", "2023-01-01")

    assert result == [{"id": 1, "name": "Method A"}, {"id": 2, "name": "Method B"}]
    mock_list_files.assert_called_once_with("/mocked/region/path", "2023-01-01")
    assert mock_open_dataset.call_count == 2


@patch("atmoswing_api.app.utils.utils.list_files")
def test_get_methods_from_netcdf_no_files(mock_list_files):
    # Mock list_files to return an empty list
    mock_list_files.return_value = []

    with pytest.raises(FileNotFoundError, match="No files found for date: 2023-01-01"):
        _get_methods_from_netcdf("/mocked/region/path", "2023-01-01")
