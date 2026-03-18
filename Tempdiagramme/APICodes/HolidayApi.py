import requests
import os
import pandas as pd
import json
import time

OUTDIR = "output_openholidays_2024"
os.makedirs(OUTDIR, exist_ok=True)

# API-Site
URL = "https://openholidaysapi.org/SchoolHolidays"
HEADERS = {"accept": "application/json"}

# Filter for States
GER_STATES = [
    "DE-BW",  # Baden-Württemberg
    "DE-BY",  # Bavaria
    "DE-BE",  # Berlin
    "DE-BB",  # Brandenburg
    "DE-HB",  # Bremen
    "DE-HH",  # Hamburg
    "DE-HE",  # Hesse
    "DE-MV",  # Mecklenburg-Vorpommern
    "DE-NI",  # Lower Saxony
    "DE-NW",  # North Rhine-Westphalia
    "DE-RP",  # Rhineland-Palatinate
    "DE-SL",  # Saarland
    "DE-SN",  # Saxony
    "DE-ST",  # Saxony-Anhalt
    "DE-SH",  # Schleswig-Holstein
    "DE-TH"   # Thuringia
]

# Filter for Date
VALID_FROM = "2024-01-01"
VALID_TO   = "2024-12-31"

all_rows = []

# Generating dictionary with Params for request
for state in GER_STATES:
    params = {
        "countryIsoCode": "DE",
        "subdivisionCode": state,
        "languageIsoCode": "EN",
        "validFrom": VALID_FROM,
        "validTo": VALID_TO
    }

    print(f"Fetching {state}...", end=" ")
    
    try:
        response = requests.get(URL, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()  # Getting JSON

        for h in data:
            holiday_name = None

            # Checking if name exist, so therefore a guaranteed way to contain all fields
            if h.get("name"):
                holiday_name = h["name"][0]["text"]

            all_rows.append({
                "state": state,
                "startDate": h.get("startDate"),
                "endDate": h.get("endDate"),
                "holiday_name": holiday_name
            })
        
        print(f"✓ ({len(data)} holidays)")
        time.sleep(0.3)  # Small delay to avoid rate limiting
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ Error: {e}")
        continue

if not all_rows:
    print("\n✗ No data fetched.")
    exit()

df = pd.DataFrame(all_rows).drop_duplicates()  # list from dictionary and delete all duplicates

df["startDate"] = pd.to_datetime(df["startDate"])  # need for pd.date_range()
df["endDate"] = pd.to_datetime(df["endDate"])

daily_rows = []

for i, row in df.iterrows():
    for day in pd.date_range(row["startDate"], row["endDate"], freq="D"):  # generating every day from start to end
        daily_rows.append({  # saves every day as a dataset
            "date": day.date().isoformat(),  # Convert to ISO format string for JSON
            "state": row["state"],
            "holiday_name": row["holiday_name"]
        })

df_daily = pd.DataFrame(daily_rows).drop_duplicates()  # new table from new dataset

# Prepare data for JSON output
json_data = {
    "metadata": {
        "country": "DE",
        "year": "2024",
        "source": "openholidaysapi.org",
        "valid_from": VALID_FROM,
        "valid_to": VALID_TO,
        "total_records": len(df_daily),
        "states": len(GER_STATES)
    },
    "holidays": df_daily.to_dict(orient="records")
}

# Save to JSON
filepath = os.path.join(OUTDIR, "school_holidays_DE_2024_daily.json")

with open(filepath, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved: {filepath}")
print(f"  Total holiday days: {len(df_daily)}")
print(f"  States covered: {len(GER_STATES)}")