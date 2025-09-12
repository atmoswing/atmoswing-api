# Script to remove the forecasts older than X days

import os
import shutil
import datetime
import argparse


parser = argparse.ArgumentParser(description="Remove forecasts older than X days.")
parser.add_argument("--data-dir", default="/app/data", help="Path to the data directory")
parser.add_argument("--keep-days", type=int, default=60, help="Number of days to keep")
args = parser.parse_args()

data_path = args.data_dir
keep_days = args.keep_days

# Compute cutoff date (inclusive keep)
cutoff_date = datetime.date.today() - datetime.timedelta(days=keep_days)

# Loop through the regions (directories) in the data directory
for region in os.listdir(data_path):
    region_path = os.path.join(data_path, region)
    if os.path.isdir(region_path):
        # Loop through the forecast directories in the region (YYYY/MM/DD)
        for year in os.listdir(region_path):
            year_path = os.path.join(region_path, year)
            if os.path.isdir(year_path):
                for month in os.listdir(year_path):
                    month_path = os.path.join(year_path, month)
                    if os.path.isdir(month_path):
                        for day in os.listdir(month_path):
                            day_path = os.path.join(month_path, day)
                            if os.path.isdir(day_path):
                                # Get the date from the directory name
                                date_str = f"{year}-{month}-{day}"
                                try:
                                    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                                except ValueError:
                                    continue
                                # Check if the date is older than the threshold
                                if date < cutoff_date:
                                    # Remove the directory
                                    shutil.rmtree(day_path)
                                    print(f"Removed directory: {day_path}")

# Remove empty directories (monthly and yearly)
for region in os.listdir(data_path):
    region_path = os.path.join(data_path, region)
    if os.path.isdir(region_path):
        for year in list(os.listdir(region_path)):
            year_path = os.path.join(region_path, year)
            if os.path.isdir(year_path):
                # Clean empty month dirs first
                for month in list(os.listdir(year_path)):
                    month_path = os.path.join(year_path, month)
                    if os.path.isdir(month_path) and not os.listdir(month_path):
                        os.rmdir(month_path)
                        print(f"Removed empty directory: {month_path}")
                # Then year dir
                if not os.listdir(year_path):
                    os.rmdir(year_path)
                    print(f"Removed empty directory: {year_path}")

# --- Remove cached JSON answers (.prebuilt_cache) older than keep-days ---
prebuilt_cache_dir = os.path.join(data_path, '.prebuilt_cache')
if os.path.isdir(prebuilt_cache_dir):
    for fname in os.listdir(prebuilt_cache_dir):
        if not fname.endswith('.json'):
            continue
        full_path = os.path.join(prebuilt_cache_dir, fname)
        # Expected pattern: {func_name}_{region}_{forecast}_{hash}.json
        core = fname[:-5]  # drop .json
        parts = core.split('_')
        if len(parts) < 4:
            continue  # not matching expected pattern
        hash_part = parts[-1]
        forecast_part = parts[-2]
        # Validate hash length (12 hex chars as per compute_cache_hash truncation)
        if len(hash_part) != 12:
            continue
        # forecast_part expected like YYYY-MM-DDTHH (safe_forecast); fallback skip
        try:
            # Only use date component for retention decision
            if 'T' in forecast_part:
                fdate = datetime.datetime.strptime(forecast_part, '%Y-%m-%dT%H').date()
            else:
                # Accept YYYY-MM-DD variant (hour-less)
                fdate = datetime.datetime.strptime(forecast_part, '%Y-%m-%d').date()
        except ValueError:
            continue
        if fdate < cutoff_date:
            try:
                os.remove(full_path)
                print(f"Removed cache file: {full_path}")
            except OSError as e:
                print(f"Failed removing cache file {full_path}: {e}")

print("Cleanup completed.")
