import os
import time
import requests
import pandas as pd
import json
# Parts of this code are LLM generated/were created with the help of LLMs
# Base URL for SMARD chart data endpoints
BASE = "https://www.smard.de/app"

# Regions to fetch data for
REGIONS = ["DE", "50Hertz", "Amprion", "TenneT", "TransnetBW"]

# Data resolution used in the API paths
RESOLUTION = "day"

# Local timezone for date conversion
TZ = "Europe/Berlin"

# Date range for the export (inclusive start, exclusive end)
START_DATE = pd.Timestamp("2024-01-01", tz=TZ)
END_EXCL = pd.Timestamp("2025-01-01", tz=TZ)

# Output directory for generated files
OUTDIR = "output_smard"
os.makedirs(OUTDIR, exist_ok=True)

# List of SMARD filter codes to request
FILTERS = [
    1223, 1224, 1225, 1226, 1227, 1228,
    4066, 4067, 4068, 4069, 4070, 4071,
    410, 4359, 4387,
    4169, 5078, 4996, 4997, 4170,
    252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262,
    3791, 123, 126, 715, 5097, 122,
    125,
]

# Human-readable names for each filter code
FILTER_NAMES = {
    1223: "Generation: Lignite",
    1224: "Generation: Nuclear",
    1225: "Generation: Wind Offshore",
    1226: "Generation: Hydropower",
    1227: "Generation: Other Conventional",
    1228: "Generation: Other Renewables",
    4066: "Generation: Biomass",
    4067: "Generation: Wind Onshore",
    4068: "Generation: PV",
    4069: "Generation: Hard Coal",
    4070: "Generation: Pumped Storage",
    4071: "Generation: Gas",
    410: "Consumption: Total (Net load)",
    4359: "Consumption: Residual load",
    4387: "Consumption: Pumped storage consumption",
    4169: "Market price: DE/LU",
    5078: "Market price: Neighbours DE/LU",
    4996: "Market price: Belgium",
    4997: "Market price: Norway 2",
    4170: "Market price: Austria",
    252: "Market price: Denmark 1",
    253: "Market price: Denmark 2",
    254: "Market price: France",
    255: "Market price: Italy (North)",
    256: "Market price: Netherlands",
    257: "Market price: Poland",
    258: "Market price: Poland (alt)",
    259: "Market price: Switzerland",
    260: "Market price: Slovenia",
    261: "Market price: Czechia",
    262: "Market price: Hungary",
    3791: "Forecast generation: Wind Offshore",
    123: "Forecast generation: Wind Onshore",
    125: "Forecast generation: PV",
    126: "Forecast generation: PV (alt)",
    715: "Forecast generation: Other",
    5097: "Forecast generation: Wind+PV",
    122: "Forecast generation: Total",
}

# Reuse one HTTP session for all requests
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; smard-downloader/1.0; +https://smard.de/)"
})


def get_json(url: str, retries: int = 5, backoff: float = 1.0):
    """
    Request JSON data from the given URL with retry handling.

    Returns:
        Parsed JSON response on success.
        None if the resource does not exist (404).

    Raises:
        The last exception encountered after all retries fail.
    """
    last_err = None

    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=30)

            # Return None if the dataset is not available
            if r.status_code == 404:
                return None

            # Retry on temporary server or rate-limit errors
            if r.status_code in (429, 502, 503, 504):
                time.sleep(backoff * (2 ** i))
                continue

            r.raise_for_status()
            return r.json()

        except Exception as e:
            last_err = e
            time.sleep(backoff * (2 ** i))

    raise last_err

#LLM generated
def fetch_filter_series_daily(filter_code: int, region: str) -> pd.DataFrame | None:
    """
    Fetch all daily time series data for one filter and one region.

    The function:
    - loads the index file containing available timestamps,
    - downloads all referenced data chunks,
    - converts timestamps to Berlin local time,
    - filters the target date range,
    - aggregates values to daily means.

    Returns:
        A DataFrame with columns: date, region, filter, name, value
        or None if no usable data is available.
    """
    index_url = f"{BASE}/chart_data/{filter_code}/{region}/index_{RESOLUTION}.json"
    idx = get_json(index_url)
    if not idx or "timestamps" not in idx:
        return None

    all_points = []

    for ts in idx["timestamps"]:
        data_url = f"{BASE}/chart_data/{filter_code}/{region}/{filter_code}_{region}_{RESOLUTION}_{ts}.json"
        js = get_json(data_url)
        if not js or "series" not in js:
            continue

        all_points.extend(js["series"])

        # Small delay to reduce request pressure on the server
        time.sleep(0.12)

    if not all_points:
        return None

    # Build a raw DataFrame from timestamp/value pairs
    df = pd.DataFrame(all_points, columns=["timestamp_ms", "value"])

    # Convert timestamps from UTC to local Berlin time
    df["datetime_utc"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df["datetime_berlin"] = df["datetime_utc"].dt.tz_convert(TZ)

    # Normalize to calendar day in local time
    df["date"] = df["datetime_berlin"].dt.floor("D")

    # Restrict data to the requested date window
    df = df[(df["date"] >= START_DATE) & (df["date"] < END_EXCL)].copy()
    if df.empty:
        return None

    # Aggregate multiple values per day to a daily mean
    df = (
        df.groupby("date", as_index=False)["value"]
        .mean()
        .sort_values("date")
    )

    # Add metadata columns for downstream processing
    df["filter"] = filter_code
    df["name"] = FILTER_NAMES.get(filter_code, str(filter_code))
    df["region"] = region

    return df[["date", "region", "filter", "name", "value"]]


# Main output structure containing metadata, region data, and availability tracking
all_data = {
    "metadata": {
        "source": "SMARD (Strommarktdaten)",
        "url": "https://www.smard.de/",
        "resolution": RESOLUTION,
        "timezone": TZ,
        "start_date": START_DATE.isoformat(),
        "end_date": END_EXCL.isoformat(),
    },
    "regions": {},
    "availability": []
}
# partly LLM generated
# Loop through all configured regions
for region in REGIONS:
    print(f"\nREGION: {region}")
    region_dfs = []
    ok, skipped = 0, 0

    # Fetch each configured filter for the current region
    for f in FILTERS:
        label = FILTER_NAMES.get(f, str(f))
        print(f"Fetching filter: {f} ({label})", end=" ")
        df_f = fetch_filter_series_daily(f, region)

        # Track unavailable datasets
        if df_f is None or df_f.empty:
            print("no data (skip)")
            all_data["availability"].append({
                "region": region,
                "filter": f,
                "name": label,
                "available": False,
                "rows": 0
            })
            skipped += 1
            continue

        # Track successfully fetched datasets
        print(f"OK ({len(df_f)} rows)")
        ok += 1
        all_data["availability"].append({
            "region": region,
            "filter": f,
            "name": label,
            "available": True,
            "rows": len(df_f)
        })
        region_dfs.append(df_f)

    print(f"Done region={region}. OK={ok}, skipped={skipped}")

    # Skip region export if no datasets were fetched
    if not region_dfs:
        print(f"WARNING: No data fetched for region={region}.")
        continue

    # Combine all filter-level DataFrames for this region
    df_region_long = pd.concat(region_dfs, ignore_index=True)

    # Convert dates to strings so the structure is JSON serializable
    region_data = df_region_long.copy()
    region_data["date"] = region_data["date"].astype(str)

    # Store the region data as a list of records
    all_data["regions"][region] = region_data.to_dict(orient="records")

    print(f"Added {len(region_data)} records for {region}")

# Write the final structured dataset to disk
json_path = os.path.join(OUTDIR, "smard_data_2024.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ All data saved to: {json_path}")
print(f" - Regions: {list(all_data['regions'].keys())}")
print(f" - Total datasets tracked: {len(all_data['availability'])}")
