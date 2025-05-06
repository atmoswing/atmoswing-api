# Script to remove the forecasts older than X days
import os
import shutil
import datetime
from pathlib import Path
from atmoswing_api import config

# Get the data path from the config
settings = config.Settings()
data_path = settings.data_dir
keep_days = settings.keep_days

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
                                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                                # Check if the date is older than the threshold
                                if (datetime.date.today() - date).days > keep_days:
                                    # Remove the directory
                                    shutil.rmtree(day_path)
                                    print(f"Removed directory: {day_path}")

# Remove empty directories (monthly and yearly)
for region in os.listdir(data_path):
    region_path = os.path.join(data_path, region)
    if os.path.isdir(region_path):
        for year in os.listdir(region_path):
            year_path = os.path.join(region_path, year)
            if os.path.isdir(year_path):
                if not os.listdir(year_path):
                    os.rmdir(year_path)
                    print(f"Removed empty directory: {year_path}")
                else:
                    for month in os.listdir(year_path):
                        month_path = os.path.join(year_path, month)
                        if os.path.isdir(month_path) and not os.listdir(month_path):
                            os.rmdir(month_path)
                            print(f"Removed empty directory: {month_path}")

print("Cleanup completed.")
