import os
import time
import requests
import pandas as pd


BASE = "https://www.smard.de/app"

# Regions we want data for: Germany and the 4 grid operators inside Germany
REGIONS = ["DE", "50Hertz", "Amprion", "TenneT", "TransnetBW"]

# Data resolution
RESOLUTION = "day"  # "quarterhour" "hour" "day" -> bruders bei hour wurde mein PC gefickt

# Time range we want to keep
START_DATE = pd.Timestamp("2023-01-01", tz="UTC")
END_EXCL   = pd.Timestamp("2023-12-31", tz="UTC") 

# Folder where the CSV files will be written
OUTDIR = "output_smard"
os.makedirs(OUTDIR, exist_ok=True)

# SMARD filter IDs (each one corresponds to a dataset)
FILTERS = [
    1223, 1224, 1225, 1226, 1227, 1228,
    4066, 4067, 4068, 4069, 4070, 4071,
    410, 4359, 4387,
    4169, 5078, 4996, 4997, 4170,
    252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262,
    3791, 123, 126, 715, 5097, 122,
    125,  # PV forecast fallback
]
# Map filter IDs to readable names so the CSV files are easier to understand
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
    410:  "Consumption: Total (Net load)",
    4359: "Consumption: Residual load",
    4387: "Consumption: Pumped storage consumption",
    4169: "Market price: DE/LU",
    5078: "Market price: Neighbours DE/LU",
    4996: "Market price: Belgium",
    4997: "Market price: Norway 2",
    4170: "Market price: Austria",
    252:  "Market price: Denmark 1",
    253:  "Market price: Denmark 2",
    254:  "Market price: France",
    255:  "Market price: Italy (North)",
    256:  "Market price: Netherlands",
    257:  "Market price: Poland",
    258:  "Market price: Poland (alt)",
    259:  "Market price: Switzerland",
    260:  "Market price: Slovenia",
    261:  "Market price: Czechia",
    262:  "Market price: Hungary",
    3791: "Forecast generation: Wind Offshore",
    123:  "Forecast generation: Wind Onshore",
    125:  "Forecast generation: PV",
    126:  "Forecast generation: PV (alt)",
    715:  "Forecast generation: Other",
    5097: "Forecast generation: Wind+PV",
    122:  "Forecast generation: Total",
}
# Use one session for all requests
SESSION = requests.Session()

# Add a user agent so requests don't look like a bot
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; smard-downloader/1.0; +https://smard.de/)"
})

def get_json(url: str, retries: int = 5, backoff: float = 1.0):
    """
    Simple helper for downloading JSON with retries.
    SMARD sometimes returns temporary errors, so we retry a few times.
    """
     
    last_err = None
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=30)

            # Dataset not available
            if r.status_code == 404:
                return None
            
            # Retry if server complains about too many requests
            if r.status_code in (429, 502, 503, 504):
                time.sleep(backoff * (2 ** i))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(backoff * (2 ** i))
    raise last_err

def fetch_filter_series_daily(filter_code: int, region: str) -> pd.DataFrame | None:
    """
    Download one dataset for a given region.
    """
    
    # First request the index file to see which data chunks exist
    index_url = f"{BASE}/chart_data/{filter_code}/{region}/index_{RESOLUTION}.json"
    idx = get_json(index_url)
    if not idx or "timestamps" not in idx:
        return None
    
    # Each timestamp corresponds to one data file
    all_points: list[list[float]] = []
    for ts in idx["timestamps"]:
        data_url = f"{BASE}/chart_data/{filter_code}/{region}/{filter_code}_{region}_{RESOLUTION}_{ts}.json"
        js = get_json(data_url)
        if not js or "series" not in js:
            continue
        
        # Append raw datapoints
        all_points.extend(js["series"])
        
        # Small pause so SMARD doesn't block the script
        time.sleep(0.12)  #delay otherwise Index error and Site forbidded downloading Data <-nur verstehen warum das gemacht wird, testet ohne timesleep für fehler

    if not all_points:
        return None
    
    # Convert raw list into dataframe
    df = pd.DataFrame(all_points, columns=["timestamp_ms", "value"])
    
    # Convert unix timestamp to readable datetime
    df["datetime_utc"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    
    # Extract just the date part
    df["date"] = df["datetime_utc"].dt.floor("D")

    # Keep only our selected time window
    df = df[(df["date"] >= START_DATE) & (df["date"] < END_EXCL)].copy()
    if df.empty:
        return None

    # Average values per day
    df = (
        df.groupby("date", as_index=False)["value"]
        .mean()
        .sort_values("date")
    )

    # Add metadata so we know what this dataset represents
    df["filter"] = filter_code
    df["name"] = FILTER_NAMES.get(filter_code, str(filter_code))
    df["region"] = region
    return df[["date", "region", "filter", "name", "value"]]

def save_region_files(region: str, df_long: pd.DataFrame):
    """
    Save results in a few different formats.
    """
    
    # Long format (good for analysis)
    long_path = os.path.join(OUTDIR, f"{region}_long.csv")
    df_long.to_csv(long_path, index=False)

    # Long format (good for analysis)
    wide_code = df_long.pivot_table(index="date", columns="filter", values="value", aggfunc="mean").sort_index()
    wide_code_path = os.path.join(OUTDIR, f"{region}_wide.csv")
    wide_code.to_csv(wide_code_path)

    # Wide format with readable names
    wide_name = df_long.pivot_table(index="date", columns="name", values="value", aggfunc="mean").sort_index()
    wide_name_path = os.path.join(OUTDIR, f"{region}_wide_by_name.csv")
    wide_name.to_csv(wide_name_path)

    return long_path, wide_code_path, wide_name_path

availability_rows = []

# Main loop over all regions
for region in REGIONS:
    print(f"\REGION: {region}")
    region_dfs = []
    ok, skipped = 0, 0

    for f in FILTERS:
        label = FILTER_NAMES.get(f, str(f))
        print(f"Fetching filter: {f} ({label})", end="")
        df_f = fetch_filter_series_daily(f, region)
        if df_f is None or df_f.empty:
            print("no data (skip)") 
            availability_rows.append({"region": region, "filter": f, "name": label, "available": 0})
            continue
        print(f"OK ({len(df_f)} rows)")
        ok += 1
        availability_rows.append({"region": region, "filter": f, "name": label, "available": 1, "rows": len(df_f)})
        region_dfs.append(df_f)

    print(f"Done region={region}. OK={ok}, skipped={skipped}") 

    if not region_dfs:
        print(f"WARNING: No data fetched for region={region}.") 
        continue

    df_region_long = pd.concat(region_dfs, ignore_index=True)
    lp, wp, wnp = save_region_files(region, df_region_long)
    print("Saved:")
    print(" -", lp)
    print(" -", wp)
    print(" -", wnp)

# Save overview of which datasets were available
df_av = pd.DataFrame(availability_rows)
av_path = os.path.join(OUTDIR, "availability_matrix.csv")
df_av.to_csv(av_path, index=False)
print("\nAvailability saved:", av_path)