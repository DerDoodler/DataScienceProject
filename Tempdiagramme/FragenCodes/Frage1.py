import json
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

TZ = "Europe/Berlin"

# --------------------------------------------------
# LOAD ELECTRICITY DATA
# --------------------------------------------------

files = [
    "smard_data_2022.json",
    "smard_data_2023.json",
    "smard_data_2024.json",
    "smard_data_2025.json"
]

all_power = []

for file in files:
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data["regions"]["DE"]
        df_temp = pd.DataFrame(records)
        all_power.append(df_temp)
        print(f"✓ Loaded {file}")
    else:
        print(f"✗ File not found: {file}")

df_power = pd.concat(all_power, ignore_index=True)

df_power["date"] = pd.to_datetime(df_power["date"], utc=True).dt.tz_convert(TZ)
df_power["date"] = df_power["date"].dt.normalize().dt.tz_localize(None)

# --------------------------------------------------
# USE ONLY TRUE ELECTRICITY DEMAND
# --------------------------------------------------

df_power = df_power[df_power["name"] == "Consumption: Total (Net load)"].copy()
df_power = df_power[["date", "value"]]
df_power.rename(columns={"value": "electricity_consumption"}, inplace=True)

# --------------------------------------------------
# LOAD HOLIDAY DATA
# --------------------------------------------------

with open("school_holidays_DE_2022-25.json", "r", encoding="utf-8") as f:
    holiday_json = json.load(f)

df_holidays = pd.DataFrame(holiday_json["holidays"])
df_holidays["date"] = pd.to_datetime(df_holidays["date"]).dt.normalize()

# --------------------------------------------------
# COUNT STATES WITH HOLIDAY
# --------------------------------------------------

holiday_counts = df_holidays.groupby("date")["state"].nunique().reset_index()
holiday_counts.rename(columns={"state": "holiday_states"}, inplace=True)

holiday_counts["is_holiday"] = (holiday_counts["holiday_states"] >= 8).astype(int)
df_holidays = holiday_counts[["date", "is_holiday"]]

# --------------------------------------------------
# MERGE DATA
# --------------------------------------------------

df = pd.merge(df_power, df_holidays, on="date", how="left")
df["is_holiday"] = df["is_holiday"].fillna(0).astype(int)

# --------------------------------------------------
# ADD WEEKDAY INFO
# --------------------------------------------------

df["weekday"] = df["date"].dt.day_name()

# --------------------------------------------------
# DAY TYPE CLASSIFICATION
# --------------------------------------------------

def categorize_day(row):
    if row["is_holiday"] == 1:
        return "Holiday"
    elif row["weekday"] == "Sunday":
        return "Sunday"
    elif row["weekday"] == "Saturday":
        return "Saturday"
    else:
        return "Weekday"

df["day_type"] = df.apply(categorize_day, axis=1)

day_order = ["Weekday", "Saturday", "Sunday", "Holiday"]
df["day_type"] = pd.Categorical(df["day_type"], categories=day_order, ordered=True)

# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

summary = df.groupby("day_type", observed=False)["electricity_consumption"].mean().reset_index()

print("\nAverage Electricity Consumption")
print(summary)

print("\nDay type counts:")
print(df["day_type"].value_counts())

# --------------------------------------------------
# 1. BOXPLOT
# --------------------------------------------------

fig_box = px.box(
    df,
    x="day_type",
    y="electricity_consumption",
    category_orders={"day_type": day_order},
    color="day_type",
    title="Electricity Consumption by Day Type",
    labels={
        "day_type": "Day Type",
        "electricity_consumption": "Electricity Consumption (MWh)"
    }
)

fig_box.update_layout(
    title=dict(x=0.5, xanchor="center"),
    showlegend=False
)

fig_box.write_html("electricity_boxplot_daytype.html", auto_open=True)

# --------------------------------------------------
# 2. BAR CHART
# --------------------------------------------------

fig_bar = px.bar(
    summary,
    x="day_type",
    y="electricity_consumption",
    color="day_type",
    category_orders={"day_type": day_order},
    title="Average Electricity Consumption by Day Type",
    labels={
        "day_type": "Day Type",
        "electricity_consumption": "Average Consumption (MWh)"
    },
    text_auto=".2f"
)

fig_bar.update_layout(
    title=dict(x=0.5, xanchor="center"),
    showlegend=False
)

fig_bar.write_html("electricity_avg_daytype.html", auto_open=True)

# --------------------------------------------------
# 3. TIME SERIES WITH HOLIDAYS
# --------------------------------------------------

fig_ts = go.Figure()

fig_ts.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["electricity_consumption"],
        mode="lines",
        name="Consumption"
    )
)

holiday_points = df[df["day_type"] == "Holiday"]

fig_ts.add_trace(
    go.Scatter(
        x=holiday_points["date"],
        y=holiday_points["electricity_consumption"],
        mode="markers",
        name="Holiday",
        marker=dict(size=7, color="red")
    )
)

fig_ts.update_layout(
    title=dict(
        text="Electricity Consumption Over Time",
        x=0.5,
        xanchor="center"
    ),
    xaxis=dict(
        title="Date",
        rangeslider=dict(visible=True)
    ),
    yaxis=dict(
        title="Consumption (MWh)"
    ),
    hovermode="x unified"
)

fig_ts.write_html("electricity_timeseries_holidays.html", auto_open=True)

print("\n" + "=" * 60)
print("✓ Analysis complete!")
print("✓ Interactive visualizations generated:")
print(" - electricity_boxplot_daytype.html")
print(" - electricity_avg_daytype.html")
print(" - electricity_timeseries_holidays.html")
print("=" * 60)
