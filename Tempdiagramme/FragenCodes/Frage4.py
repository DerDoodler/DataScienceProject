import json
import pandas as pd
import numpy as np
import os
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================================================
# LOAD ALL DATA
# ============================================================================

smard_files = [
    "smard_data_2022.json",
    "smard_data_2023.json",
    "smard_data_2024.json",
    "smard_data_2025.json"
]

all_power_data = []

for file in smard_files:
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                smard = json.load(f)

            df_temp = pd.DataFrame(smard["regions"]["DE"])
            all_power_data.append(df_temp)

            print(f"✓ Loaded {file}")

        except Exception as e:
            print(f"✗ Error loading {file}: {e}")

df_power = pd.concat(all_power_data, ignore_index=True)
TZ = "Europe/Berlin"

df_power["date"] = (
    pd.to_datetime(df_power["date"], utc=True)
    .dt.tz_convert(TZ)
    .dt.normalize()
    .dt.tz_localize(None)
)

# ============================================================================
# LOAD WEATHER DATA
# ============================================================================

weather_file = "weather_data22-25.json"

if os.path.exists(weather_file):

    with open(weather_file, "r", encoding="utf-8") as f:
        weather = json.load(f)

    df_weather = pd.DataFrame(weather["regions"]["DE"])
    df_weather["date"] = pd.to_datetime(df_weather["date"]).dt.tz_localize(None)

    if "sunshine_duration_s" in df_weather.columns:
        df_weather["sunshine_duration_h"] = df_weather["sunshine_duration_s"] / 3600
        df_weather = df_weather[
            ["date", "wind_max_kmh", "temp_max_c", "precipitation_sum_mm", "sunshine_duration_h"]
        ]
    else:
        df_weather = df_weather[
            ["date", "wind_max_kmh", "temp_max_c", "precipitation_sum_mm"]
        ]

else:
    print(f"✗ Weather file not found: {weather_file}")
    exit()

# ============================================================================
# QUESTION 2: GENERATION MIX SHIFT ON HIGH RENEWABLE DAYS
# ============================================================================

print("\n" + "=" * 80)
print("QUESTION 2: Generation Mix Shift on High Renewable Output Days")
print("=" * 80)

df_gen_all = df_power.pivot_table(
    index="date",
    columns="name",
    values="value"
).reset_index()

df_q2 = pd.merge(df_gen_all, df_weather[["date"]], on="date")

renewable_cols = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV"
]

df_q2["renewable_total"] = df_q2[renewable_cols].sum(axis=1)

high_renewable_threshold = df_q2["renewable_total"].quantile(0.75)

df_q2["high_renewable"] = df_q2["renewable_total"] >= high_renewable_threshold

print(f"\nHigh Renewable Threshold (75th percentile): {high_renewable_threshold:.0f} MWh")
print(f"Days with high renewable output: {df_q2['high_renewable'].sum()} / {len(df_q2)}")

conventional_cols = [
    "Generation: Lignite",
    "Generation: Hard Coal",
    "Generation: Gas",
    "Generation: Nuclear"
]

high_renewable_days = df_q2[df_q2["high_renewable"]]
low_renewable_days = df_q2[~df_q2["high_renewable"]]

mix_high = high_renewable_days[conventional_cols].mean()
mix_low = low_renewable_days[conventional_cols].mean()

print("\nAverage Generation on High Renewable Days:")
for col in conventional_cols:
    print(f"{col}: {mix_high[col]:.0f} MWh")

print("\nAverage Generation on Low Renewable Days:")
for col in conventional_cols:
    print(f"{col}: {mix_low[col]:.0f} MWh")

pct_change = []

print("\nChange in Generation (High vs Low Renewable Days):")

for col in conventional_cols:

    change = (
        (mix_high[col] - mix_low[col]) / mix_low[col] * 100
        if mix_low[col] > 0 else 0
    )

    pct_change.append(change)

    print(f"{col}: {change:+.1f}%")

# ============================================================================
# PLOTLY VISUALIZATIONS
# ============================================================================

mix_df = pd.DataFrame({
    "Source": conventional_cols,
    "High Renewable Days": mix_high.values,
    "Low Renewable Days": mix_low.values
})

fig1 = px.bar(
    mix_df,
    x="Source",
    y=["High Renewable Days", "Low Renewable Days"],
    barmode="group",
    title="Generation Mix: High vs Low Renewable Days",
    labels={"value": "Average Generation (MWh)", "Source": "Energy Source"}
)

fig1.update_layout(
    title=dict(
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    yaxis=dict(
        title=dict(font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    )
)

fig1.write_html("q2_generation_mix.html", auto_open=True)

pct_df = pd.DataFrame({
    "Source": conventional_cols,
    "Percentage Change": pct_change
})

fig2 = px.bar(
    pct_df,
    x="Percentage Change",
    y="Source",
    orientation="h",
    text="Percentage Change",
    title="How Conventional Sources Change on High Renewable Days"
)

fig2.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside",
    textfont=dict(size=15)
)

fig2.update_layout(
    title=dict(
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    yaxis=dict(
        title=dict(font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    showlegend=False
)

fig2.write_html("q2_conventional_change.html", auto_open=True)

# ============================================================================
# SAVE + OPEN IN BROWSER
# ============================================================================

print("\n" + "=" * 80)
print("✓ Analysis complete!")
print("✓ Interactive plot saved and opened in browser.")
print("=" * 80)
