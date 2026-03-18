import json
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# LOAD DATA
# -----------------------------

TZ = "Europe/Berlin"

smard_files = [
    "smard_data_2022.json",
    "smard_data_2023.json",
    "smard_data_2024.json",
    "smard_data_2025.json"
]

all_smard_data = {}
tsos = ["50Hertz", "Amprion", "TenneT", "TransnetBW", "DE"]

for tso in tsos:
    all_smard_data[tso] = []

for file in smard_files:
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                smard = json.load(f)

            for region in tsos:
                if region in smard["regions"]:
                    df_temp = pd.DataFrame(smard["regions"][region])
                    all_smard_data[region].append(df_temp)

            print(f"✓ Loaded {file}")

        except Exception as e:
            print(f"✗ Error loading {file}: {e}")
    else:
        print(f"✗ File not found: {file}")

# Combine yearly datasets
dfs_tso_power = {}

for region in tsos:
    if all_smard_data[region]:
        dfs_tso_power[region] = pd.concat(all_smard_data[region], ignore_index=True)
        dfs_tso_power[region]["date"] = (
            pd.to_datetime(dfs_tso_power[region]["date"], utc=True)
            .dt.tz_convert(TZ)
            .dt.normalize()
            .dt.tz_localize(None)
        )

# -----------------------------
# LOAD WEATHER DATA
# -----------------------------

weather_file = "weather_data22-25.json"

if os.path.exists(weather_file):

    with open(weather_file, "r", encoding="utf-8") as f:
        weather = json.load(f)

    dfs_tso_weather = {}

    for tso in tsos:
        if tso in weather["regions"]:
            dfs_tso_weather[tso] = pd.DataFrame(weather["regions"][tso])
            dfs_tso_weather[tso]["date"] = (
                pd.to_datetime(dfs_tso_weather[tso]["date"], utc=True)
                .dt.tz_convert(TZ)
                .dt.normalize()
                .dt.tz_localize(None)
            )

    print(f"✓ Loaded {weather_file}")

else:
    print(f"✗ Weather file not found: {weather_file}")
    exit()

df_de_power = dfs_tso_power.get("DE")
df_de_weather = dfs_tso_weather.get("DE")

print("\nData loaded successfully!")
print(f"Date range: {df_de_power['date'].min()} to {df_de_power['date'].max()}")

for tso in tsos:
    if tso in dfs_tso_power:
        dfs_tso_power[tso]["year"] = dfs_tso_power[tso]["date"].dt.year
    if tso in dfs_tso_weather:
        dfs_tso_weather[tso]["year"] = dfs_tso_weather[tso]["date"].dt.year

tsos = ["50Hertz", "Amprion", "TenneT", "TransnetBW"]

# -----------------------------
# INTERACTIVE GENERATION MIX WITH DROPDOWN
# -----------------------------

generation_types = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV",
    "Generation: Hydropower",
    "Generation: Biomass",
    "Generation: Lignite",
    "Generation: Nuclear",
    "Generation: Gas",
    "Generation: Hard Coal"
]

all_regions = ["DE"] + tsos
region_mix = {}

for region in all_regions:

    if region == "DE":
        df = df_de_power
    else:
        df = dfs_tso_power.get(region)

    if df is None:
        continue

    gen = (
        df[df["name"].isin(generation_types)]
        .groupby("name")["value"]
        .mean()
        .sort_values(ascending=False)
    )

    region_mix[region] = gen

# start figure with Germany
first_region = all_regions[0]

fig_mix = go.Figure(
    data=[go.Pie(
        labels=[x.replace("Generation: ", "") for x in region_mix[first_region].index],
        values=region_mix[first_region].values
    )]
)

# dropdown menu
buttons = []

for region in all_regions:

    labels = [x.replace("Generation: ", "") for x in region_mix[region].index]
    values = region_mix[region].values

    buttons.append(
        dict(
            label=region,
            method="update",
            args=[{
                "labels": [labels],
                "values": [values]
            },
            {
                "title": {
                    "text": f"Average Generation Mix ({region}) 2022–2025",
                    "x": 0.5,
                    "xanchor": "center",
                    "y": 0.95,
                    "yanchor": "top",
                    "font": {"size": 24}
                }
            }]
        )
    )

fig_mix.update_layout(
    title=dict(
        text=f"Average Generation Mix ({first_region}) 2022–2025",
        x=0.5,
        xanchor="center",
        y=0.95,
        yanchor="top",
        font=dict(size=24)
    ),
    font=dict(size=15),
    margin=dict(t=120),
    legend=dict(font=dict(size=15)),
    updatemenus=[
        dict(
            buttons=buttons,
            direction="down",
            showactive=True,
            x=0.02,
            y=1.18,
            xanchor="left",
            yanchor="top",
            font=dict(size=15)
        )
    ]
)

fig_mix.write_html("generation_mix_dropdown.html", auto_open=True)

# -----------------------------
# 2. GENERATION BY TYPE ACROSS REGIONS
# -----------------------------

monthly_gen = {}

key_gen = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV",
    "Generation: Hydropower",
    "Generation: Nuclear",
    "Generation: Lignite"
]

for region in all_regions:

    if region == "DE":
        df = df_de_power
    else:
        df = dfs_tso_power.get(region)

    if df is None:
        continue

    df_month = df[df["name"].isin(key_gen)]

    monthly_avg = (
        df_month.groupby("name")["value"]
        .mean()
        .sort_values(ascending=False)
    )

    monthly_gen[region] = monthly_avg

monthly_gen_df = pd.DataFrame(monthly_gen).T

fig_region = px.bar(
    monthly_gen_df,
    barmode="group",
    title="Average Generation by Source Across Regions (2022–2025)",
    labels={"value": "Average Generation (MWh)", "index": "Region"}
)

fig_region.update_layout(
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

fig_region.write_html("generation_by_region.html", auto_open=True)

# -----------------------------
# 3. RENEWABLE VS FOSSIL MIX
# -----------------------------

renewable_types = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV",
    "Generation: Hydropower",
    "Generation: Biomass"
]

fossil_types = [
    "Generation: Lignite",
    "Generation: Nuclear",
    "Generation: Hard Coal",
    "Generation: Gas"
]

renewable_data = {}
fossil_data = {}

for region in all_regions:

    if region == "DE":
        df = df_de_power
    else:
        df = dfs_tso_power.get(region)

    if df is None:
        continue

    renewable = (
        df[df["name"].isin(renewable_types)]["value"].mean()
    )

    fossil = (
        df[df["name"].isin(fossil_types)]["value"].mean()
    )

    renewable_data[region] = renewable
    fossil_data[region] = fossil

renewable_fossil_df = pd.DataFrame({
    "Renewable": renewable_data,
    "Fossil": fossil_data
})

fig_rf = px.bar(
    renewable_fossil_df,
    barmode="stack",
    title="Renewable vs Fossil Generation Mix (2022–2025)",
    labels={"value": "Average Generation (MWh)", "index": "Region"}
)

fig_rf.update_layout(
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

fig_rf.write_html("renewable_vs_fossil.html", auto_open=True)

print("\n" + "=" * 60)
print("✓ Analysis complete!")
print("✓ Interactive visualizations generated:")
print(" - generation_mix_regions.html")
print(" - generation_by_region.html")
print(" - renewable_vs_fossil.html")
print("=" * 60)
