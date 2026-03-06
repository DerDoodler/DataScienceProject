import os
import requests
import pandas as pd

# Function to download daily weather data for a specific location
def get_weather_daily(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    
    # Open-Meteo archive endpoint for historical weather data
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    # Parameters sent to the API request
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,windspeed_10m_max",
        "timezone": "Europe/Berlin"
    }

    # Send request to API. Stop program if request failed
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()

    # Convert JSON data into a pandas DataFrame
    j = r.json()

    # Convert JSON data into a pandas DataFrame
    df = pd.DataFrame({
        "date": j["daily"]["time"],
        "precipitation_sum_mm": j["daily"]["precipitation_sum"],
        "temp_max_c": j["daily"]["temperature_2m_max"],
        "temp_min_c": j["daily"]["temperature_2m_min"],
        "wind_max_kmh": j["daily"]["windspeed_10m_max"],
    })
    df["date"] = pd.to_datetime(df["date"])
    return df

# Time period we want to download
start = "2023-01-01"
end   = "2023-12-31"

# Main output folder
OUTDIR = "output_weather_openmeteo_2023"
# Create folder if it doesn't exist
os.makedirs(OUTDIR, exist_ok=True)

# Major Cities grouped by German power grid regions
regions = {
    "50Hertz": [
        ("Berlin", 52.5200, 13.4050),
        ("Hamburg", 53.5511, 9.9937),
        ("Leipzig", 51.3397, 12.3731),
        ("Dresden", 51.0504, 13.7373),
        ("Rostock", 54.0924, 12.0991),
    ],
    "TenneT": [
        ("Hannover", 52.3759, 9.7320),
        ("Bremen", 53.0793, 8.8017),
        ("Kassel", 51.3127, 9.4797),
        ("Nürnberg", 49.4521, 11.0767),
        ("München", 48.1351, 11.5820),
    ],
    "Amprion": [
        ("Köln", 50.9375, 6.9603),
        ("Dortmund", 51.5136, 7.4653),
        ("Düsseldorf", 51.2277, 6.7735),
        ("Essen", 51.4556, 7.0116),
        ("Frankfurt", 50.1109, 8.6821),
    ],
    "TransnetBW": [
        ("Stuttgart", 48.7758, 9.1829),
        ("Karlsruhe", 49.0069, 8.4037),
        ("Freiburg", 47.9990, 7.8421),
        ("Mannheim", 49.4875, 8.4660),
        ("Ulm", 48.4011, 9.9876),
    ],
}

# Option to also calculate a Germany-wide average
include_DE_overall = True

# Loop through all regions
all_city_dfs_for_DE = []

# Loop through all regions
for region, cities in regions.items():
    print(f"\n{region}") # show which region is currently processed
    city_dfs = []

    # Create subfolder for this region
    region_dir = os.path.join(OUTDIR, region)
    os.makedirs(region_dir, exist_ok=True)

    # Loop through all cities inside the region
    for city, lat, lon in cities:
        print(f"Load {city} ...")

        # Download weather data
        df_city = get_weather_daily(lat, lon, start, end)

        # Add region and city columns
        df_city["region"] = region
        df_city["city"] = city
        city_dfs.append(df_city)

        # Save city data as CSV (optional but useful for debugging)
        city_path = os.path.join(region_dir, f"weather_{city}_2023_daily.csv")
        df_city.to_csv(city_path, index=False, encoding="utf-8")

    # Calculate daily average across the cities in this region
    df_region = pd.concat(city_dfs, ignore_index=True)
    df_region_avg = df_region.groupby("date", as_index=False).mean(numeric_only=True)
    df_region_avg["region"] = region

    region_avg_path = os.path.join(OUTDIR, f"weather_{region}_AVG_2023_daily.csv")
    df_region_avg.to_csv(region_avg_path, index=False, encoding="utf-8")

    print("saved:")
    print(" -", region_avg_path)

    if include_DE_overall:
        all_city_dfs_for_DE.append(df_region)

# Calculate overall Germany average (all cities combined)
if include_DE_overall and all_city_dfs_for_DE:
    df_all = pd.concat(all_city_dfs_for_DE, ignore_index=True)
    df_DE_avg = df_all.groupby("date", as_index=False).mean(numeric_only=True)
    df_DE_avg["region"] = "DE"

    de_path = os.path.join(OUTDIR, "weather_DE_AVG_2023_daily.csv")
    df_DE_avg.to_csv(de_path, index=False, encoding="utf-8")
    print(" -", de_path)

print("\nsaved", OUTDIR)