import requests
import pandas as pd

#API-Site
URL = "https://openholidaysapi.org/SchoolHolidays"
HEADERS = {"accept": "text/json"} #ensure JSON response

#Filter for States
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

#filter for Date
VALID_FROM = "2023-01-01"
VALID_TO   = "2023-12-31"

all_rows = []

#generating dictionary with Params for request
for state in GER_STATES:
    params = {
        "countryIsoCode": "DE",
        "subdivisionCode": state,
        "languageIsoCode": "EN",
        "validFrom": VALID_FROM,
        "validTo": VALID_TO
    }

    response = requests.get(URL, params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json() #getting JSON

    
    for h in data: 

        holiday_name = None

        #cheking if name exist, so therefore a guaranteed way to contain all fields
        if h.get("name"):
            holiday_name = h["name"][0]["text"]

        all_rows.append({
            "state": state,
            "startDate": h.get("startDate"),
            "endDate": h.get("endDate"),
            "holiday_name": holiday_name
        })    

df = pd.DataFrame(all_rows).drop_duplicates() #list from dictionary and delete all duplicates

df["startDate"] = pd.to_datetime(df["startDate"]) #need for pd.date_range()
df["endDate"] = pd.to_datetime(df["endDate"])

daily_rows = []

for i, row in df.iterrows():
    for day in pd.date_range(row["startDate"], row["endDate"], freq="D"): #generating every day from start to end with given Param
        daily_rows.append({ #saves every day as a Dataset
            "date": day.date(),
            "state": row["state"],
            "holiday_name": row["holiday_name"]
        })
#Structure Example: 
#date           state     holiday_name
#2023-07-17     DE-SH     Summer Holidays

df_daily = pd.DataFrame(daily_rows).drop_duplicates() #new Table from new Dataset

#making a folder for better order
filepath = os.path.join(OUTDIR, "school_holidays_DE_2023_daily.csv")

df_daily.to_csv(
    filepath,
    index=False,
    encoding="utf-8"
)

print("saved:")
print(filepath)
