import pytest
import os
from unittest.mock import patch, MagicMock

from atmoswing_api.app.services.meta import get_last_forecast_date_from_files, \
    _get_last_forecast_date, get_method_list, _get_methods_from_netcdf, \
    get_method_configs_list, get_entities_list

# Path to the data directory
cwd = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(cwd, "data")


@pytest.mark.asyncio
@patch("atmoswing_api.app.services.meta._get_last_forecast_date")
@patch("atmoswing_api.app.utils.utils.check_region_path")
async def test_get_last_forecast_date_from_files_mock(mock_check_region_path, mock_get_last_forecast_date):
    # Mock check_region_path
    mock_check_region_path.return_value = "/mocked/region/path"

    # Mock _get_last_forecast_date
    mock_get_last_forecast_date.return_value = "2023-01-01T12"

    result = await get_last_forecast_date_from_files("/mocked/data_dir", "region")

    assert result == {"last_forecast_date": "2023-01-01T12"}
    mock_check_region_path.assert_called_once_with("/mocked/data_dir", "region")
    mock_get_last_forecast_date.assert_called_once_with("/mocked/region/path")


@pytest.mark.asyncio
async def test_get_last_forecast_date_from_files():
    result = await get_last_forecast_date_from_files(data_dir, "adn")

    assert result == {"last_forecast_date": "2024-10-06T18"}


@patch("os.listdir")
@patch("atmoswing_api.app.utils.utils.convert_to_datetime")
def test_get_last_forecast_date_mock(mock_convert_to_datetime, mock_listdir):
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

    with pytest.raises(ValueError, match="Invalid date format"):
        _get_last_forecast_date("/mocked/region/path")


@pytest.mark.asyncio
@patch("atmoswing_api.app.services.meta._get_methods_from_netcdf")
@patch("atmoswing_api.app.utils.utils.check_region_path")
async def test_get_method_list_mock(mock_check_region_path, mock_get_methods):
    # Mock check_region_path
    mock_check_region_path.return_value = "/mocked/region/path"

    # Mock _get_methods_from_netcdf
    mock_get_methods.return_value = [
        {"id": 1, "name": "Method A"},
        {"id": 2, "name": "Method B"},
    ]

    result = await get_method_list("/mocked/data_dir", "region", "2023-01-01")

    assert result == [{"id": 1, "name": "Method A"}, {"id": 2, "name": "Method B"}]
    mock_check_region_path.assert_called_once_with("/mocked/data_dir", "region")
    mock_get_methods.assert_called_once_with("/mocked/region/path", "2023-01-01")


@pytest.mark.asyncio
async def test_get_method_list():
    result = await get_method_list(data_dir, "adn", "2024-10-06")

    assert result[0] == {'id': '2Z-06h-GFS', 'name': 'Analogie circulation (2Z) 6h GFS'}
    assert result[5] == {'id': '4Zo-CEP', 'name': 'Analogie circulation (4Zo) CEP'}


@patch("atmoswing_api.app.utils.utils.list_files")
@patch("xarray.open_dataset")
def test_get_methods_from_netcdf_mock(mock_open_dataset, mock_list_files):
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


@pytest.mark.asyncio
@patch("xarray.open_dataset")
@patch("atmoswing_api.app.utils.utils.list_files")
@patch("atmoswing_api.app.utils.utils.check_region_path")
async def test_get_method_configs_list_mock(
    mock_check_region_path, mock_list_files, mock_open_dataset
):
    # Mock check_region_path to return a mocked path
    mock_check_region_path.return_value = "/mocked/region/path"

    # Mock list_files to return mocked file paths
    mock_list_files.return_value = ["/mocked/file1.nc", "/mocked/file2.nc", "/mocked/file3.nc"]

    # Mock NetCDF datasets
    mock_ds1 = MagicMock()
    mock_ds1.method_id = 1
    mock_ds1.method_id_display = "Method A"
    mock_ds1.specific_tag = "Alpes_Nord"
    mock_ds1.specific_tag_display = "Alpes du Nord"
    mock_ds1.__enter__.return_value = mock_ds1  # Handle context manager

    mock_ds2 = MagicMock()
    mock_ds2.method_id = 2
    mock_ds2.method_id_display = "Method B"
    mock_ds2.specific_tag = "Alpes_Nord"
    mock_ds2.specific_tag_display = "Alpes du Nord"
    mock_ds2.__enter__.return_value = mock_ds2  # Handle context manager

    mock_ds3 = MagicMock()
    mock_ds3.method_id = 1
    mock_ds3.method_id_display = "Method A"
    mock_ds3.specific_tag = "Alpes_Sud"
    mock_ds3.specific_tag_display = "Alpes du Sud"
    mock_ds3.__enter__.return_value = mock_ds3  # Handle context manager

    mock_open_dataset.side_effect = [mock_ds1, mock_ds2, mock_ds3]

    result = await get_method_configs_list("/mocked/data/dir", "region1", "2023-01-01")

    # Assert the result
    expected_result = [
        {
            "id": 1,
            "name": "Method A",
            "configurations": [
                {"id": "Alpes_Nord", "name": "Alpes du Nord"},
                {"id": "Alpes_Sud", "name": "Alpes du Sud"}
            ],
        },
        {
            "id": 2,
            "name": "Method B",
            "configurations": [{"id": "Alpes_Nord", "name": "Alpes du Nord"}],
        },
    ]
    assert result == expected_result

    # Ensure the mocked methods were called with expected arguments
    mock_check_region_path.assert_called_once_with("/mocked/data/dir", "region1")
    mock_list_files.assert_called_once_with("/mocked/region/path", "2023-01-01")
    mock_open_dataset.assert_any_call("/mocked/file1.nc")
    mock_open_dataset.assert_any_call("/mocked/file2.nc")


@pytest.mark.asyncio
async def test_get_method_configs_list():
    result = await get_method_configs_list(data_dir, "adn", "2024-10-06")

    assert result[0] == {
        'configurations': [
            {'id': 'Alpes_Nord', 'name': 'Alpes du Nord'}
        ],
        'id': '2Z-06h-GFS', 'name': 'Analogie circulation (2Z) 6h GFS'}
    assert result[6] == {
        'configurations': [
            {'id': 'Alpes_Nord', 'name': 'Alpes du Nord'},
            {'id': 'Alpes_Sud', 'name': 'Alpes du Sud'}
        ],
        'id': '4Zo-GFS', 'name': 'Analogie circulation (4Zo) GFS'}


@pytest.mark.asyncio
@patch("atmoswing_api.app.utils.utils.check_region_path")
@patch("atmoswing_api.app.utils.utils.get_file_path")
@patch("xarray.open_dataset")
@patch("os.path.exists")
async def test_get_entities_list_mock(
    mock_exists, mock_open_dataset, mock_get_file_path, mock_check_region_path
):
    # Mock inputs
    data_dir = "/mocked/data/dir"
    region = "region1"
    date = "2023-01-01"
    method = "method1"
    configuration = "config1"

    # Mocked outputs
    region_path = "/mocked/region/path"
    file_path = "/mocked/region/path/2023-01-01_method1_config1.nc"

    # Mock the utils functions
    mock_check_region_path.return_value = region_path
    mock_get_file_path.return_value = file_path
    mock_exists.return_value = True

    # Mock the NetCDF dataset content
    mock_ds = MagicMock()
    mock_ds.station_ids.values = [1, 2, 3]
    mock_ds.station_official_ids.values = ["official1", "official2", None]
    mock_ds.station_names.values = ["Station A", "Station B", "Station C"]
    mock_ds.station_x_coords.values = [100.0, 200.0, 300.0]
    mock_ds.station_y_coords.values = [400.0, 500.0, 600.0]
    mock_ds.__enter__.return_value = mock_ds  # Handle context manager
    mock_open_dataset.return_value = mock_ds

    # Call the async function under test
    result = await get_entities_list(data_dir, region, date, method, configuration)

    # Expected result
    expected_result = [
        {
            "id": 1,
            "name": "Station A",
            "x": 100.0,
            "y": 400.0,
            "official_id": "official1",
        },
        {
            "id": 2,
            "name": "Station B",
            "x": 200.0,
            "y": 500.0,
            "official_id": "official2",
        },
        {
            "id": 3,
            "name": "Station C",
            "x": 300.0,
            "y": 600.0,
        },
    ]

    # Assertions
    assert result == expected_result
    mock_check_region_path.assert_called_once_with(data_dir, region)
    mock_get_file_path.assert_called_once_with(region_path, date, method, configuration)
    mock_exists.assert_called_once_with(file_path)
    mock_open_dataset.assert_called_once_with(file_path)


@pytest.mark.asyncio
async def test_get_entities_list():
    # Mock inputs
    region = "adn"
    date = "2024-10-05T00"
    method = "4Zo-GFS"
    configuration = "Alpes_Nord"

    # Call the async function under test
    result = await get_entities_list(data_dir, region, date, method, configuration)

    # Assertions
    assert result[0] == {
        "id": 1,
        "name": "Arly",
        "x": 973795,
        "y": 6524123
    }

    assert result[5] == {
        "id": 6,
        "name": "Haute Maurienne",
        "x": 1006560,
        "y": 6473617
    }
