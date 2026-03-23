import requests
import os
import pandas as pd
import json
import time
# Parts of this code are LLM generated/were created with the help of LLMs
# Output directory for exported holiday data
OUTDIR = "output_openholidays_2024"
os.makedirs(OUTDIR, exist_ok=True)

# API endpoint and request headers
URL = "https://openholidaysapi.org/SchoolHolidays"
HEADERS = {"accept": "application/json"}

# German federal states (subdivision codes)
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

# Date range for the holiday request
VALID_FROM = "2024-01-01"
VALID_TO = "2024-12-31"

# Collect all holiday periods returned by the API
all_rows = []

# Request school holidays for each German state
for state in GER_STATES:
    params = {
        "countryIsoCode": "DE",
        "subdivisionCode": state,
        "languageIsoCode": "EN",
        "validFrom": VALID_FROM,
        "validTo": VALID_TO
    }

    print(f"Fetching {state}...", end=" ")
    #LLM generated
    try:
        # Send request and raise an error for unsuccessful responses
        response = requests.get(URL, params=params, headers=HEADERS)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract relevant fields from each holiday entry
        for h in data:
            holiday_name = None

            # Use the first available holiday name if present
            if h.get("name"):
                holiday_name = h["name"][0]["text"]

            all_rows.append({
                "state": state,
                "startDate": h.get("startDate"),
                "endDate": h.get("endDate"),
                "holiday_name": holiday_name
            })

        print(f"✓ ({len(data)} holidays)")

        # Small delay to reduce the chance of rate limiting
        time.sleep(0.3)

    except requests.exceptions.HTTPError as e:
        print(f"✗ Error: {e}")
        continue

# Stop execution if no holiday data was fetched
if not all_rows:
    print("\n✗ No data fetched.")
    exit()

# Create a DataFrame from the collected holiday periods and remove duplicates
df = pd.DataFrame(all_rows).drop_duplicates()

# Convert date columns to datetime format for range expansion
df["startDate"] = pd.to_datetime(df["startDate"])
df["endDate"] = pd.to_datetime(df["endDate"])

# Expand each holiday period into individual daily records
daily_rows = []

for i, row in df.iterrows():
    for day in pd.date_range(row["startDate"], row["endDate"], freq="D"):
        daily_rows.append({
            # Store each holiday day as an ISO date string
            "date": day.date().isoformat(),
            "state": row["state"],
            "holiday_name": row["holiday_name"]
        })

# Create the final daily-level holiday table and remove duplicates
df_daily = pd.DataFrame(daily_rows).drop_duplicates()

# Build the JSON output structure with metadata and records
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

# Save the result as a formatted JSON file
filepath = os.path.join(OUTDIR, "school_holidays_DE_2024_daily.json")

with open(filepath, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

# Print summary information after export
print(f"\n✓ Saved: {filepath}")
print(f" Total holiday days: {len(df_daily)}")
print(f" States covered: {len(GER_STATES)}")
