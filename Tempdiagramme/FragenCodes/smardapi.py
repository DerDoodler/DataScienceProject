import os
import time
import requests
import pandas as pd
import json

BASE = "https://www.smard.de/app"

REGIONS = ["DE", "50Hertz", "Amprion", "TenneT", "TransnetBW"]
RESOLUTION = "day"

TZ = "Europe/Berlin"

START_DATE = pd.Timestamp("2024-01-01", tz=TZ)
END_EXCL = pd.Timestamp("2025-01-01", tz=TZ)

OUTDIR = "output_smard"
os.makedirs(OUTDIR, exist_ok=True)

FILTERS = [
    1223, 1224, 1225, 1226, 1227, 1228,
    4066, 4067, 4068, 4069, 4070, 4071,
    410, 4359, 4387,
    4169, 5078, 4996, 4997, 4170,
    252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262,
    3791, 123, 126, 715, 5097, 122,
    125,
]

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

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; smard-downloader/1.0; +https://smard.de/)"
})

def get_json(url: str, retries: int = 5, backoff: float = 1.0):
    last_err = None
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=30)

            if r.status_code == 404:
                return None

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
        time.sleep(0.12)

    if not all_points:
        return None

    df = pd.DataFrame(all_points, columns=["timestamp_ms", "value"])

    df["datetime_utc"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df["datetime_berlin"] = df["datetime_utc"].dt.tz_convert(TZ)

    df["date"] = df["datetime_berlin"].dt.floor("D")

    df = df[(df["date"] >= START_DATE) & (df["date"] < END_EXCL)].copy()
    if df.empty:
        return None

    df = (
        df.groupby("date", as_index=False)["value"]
        .mean()
        .sort_values("date")
    )

    df["filter"] = filter_code
    df["name"] = FILTER_NAMES.get(filter_code, str(filter_code))
    df["region"] = region
    return df[["date", "region", "filter", "name", "value"]]

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

for region in REGIONS:
    print(f"\nREGION: {region}")
    region_dfs = []
    ok, skipped = 0, 0

    for f in FILTERS:
        label = FILTER_NAMES.get(f, str(f))
        print(f"Fetching filter: {f} ({label})", end=" ")
        df_f = fetch_filter_series_daily(f, region)

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

    if not region_dfs:
        print(f"WARNING: No data fetched for region={region}.")
        continue

    df_region_long = pd.concat(region_dfs, ignore_index=True)
    region_data = df_region_long.copy()
    region_data["date"] = region_data["date"].astype(str)
    all_data["regions"][region] = region_data.to_dict(orient="records")

    print(f"Added {len(region_data)} records for {region}")

json_path = os.path.join(OUTDIR, "smard_data_2024.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ All data saved to: {json_path}")
print(f" - Regions: {list(all_data['regions'].keys())}")
print(f" - Total datasets tracked: {len(all_data['availability'])}")