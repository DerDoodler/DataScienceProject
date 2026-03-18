import json
import pandas as pd
import numpy as np
import os

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------
# LOAD ALL SMARD ELECTRICITY DATA
# -----------------------------

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

    else:
        print(f"✗ File not found: {file}")

df_power = pd.concat(all_power_data, ignore_index=True)
TZ = "Europe/Berlin"
# Richtiges Zeitformat: erst UTC, dann Berlin-Zeit
df_power["date"] = pd.to_datetime(df_power["date"], utc=True).dt.tz_convert(TZ)

# Optional: nur Kalendertag behalten, damit Merge mit Feiertagen sauber ist
df_power["date"] = df_power["date"].dt.normalize().dt.tz_localize(None)

generation_types = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV"
]

df_power = df_power[df_power["name"].isin(generation_types)]

df_power = df_power.pivot_table(
    index="date",
    columns="name",
    values="value"
).reset_index()

df_power = df_power.rename(columns={
    "Generation: Wind Onshore": "wind_onshore",
    "Generation: Wind Offshore": "wind_offshore",
    "Generation: PV": "solar"
})

df_power["wind_total"] = df_power["wind_onshore"] + df_power["wind_offshore"]

print(f"\nPower data loaded: {len(df_power)} days")

# -----------------------------
# LOAD WEATHER DATA
# -----------------------------

weather_file = "weather_data22-25.json"

if os.path.exists(weather_file):

    with open(weather_file, "r", encoding="utf-8") as f:
        weather = json.load(f)

    df_weather = pd.DataFrame(weather["regions"]["DE"])

    df_weather["date"] = pd.to_datetime(df_weather["date"]).dt.tz_localize(None)

    if "sunshine_duration_s" in df_weather.columns:

        df_weather["sunshine_duration_h"] = df_weather["sunshine_duration_s"] / 3600

        df_weather = df_weather[
            ["date","wind_max_kmh","temp_max_c",
             "precipitation_sum_mm","sunshine_duration_h"]
        ]

    else:

        df_weather = df_weather[
            ["date","wind_max_kmh","temp_max_c",
             "precipitation_sum_mm"]
        ]

    print(f"Weather data loaded: {len(df_weather)} days")

else:
    print("Weather file not found")
    exit()

# -----------------------------
# MERGE DATASETS
# -----------------------------

df = pd.merge(df_power, df_weather, on="date")

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["quarter"] = df["date"].dt.quarter
df["day_of_year"] = df["date"].dt.dayofyear

print(f"Merged dataset: {len(df)} days")
# -----------------------------
# CORRELATION MATRIX
# -----------------------------

weather_cols = ["wind_max_kmh","temp_max_c","precipitation_sum_mm"]

if "sunshine_duration_h" in df.columns:
    weather_cols.append("sunshine_duration_h")

generation_cols = ["wind_onshore","wind_offshore","solar","wind_total"]

corr_matrix = pd.DataFrame(index=weather_cols, columns=generation_cols)

for w in weather_cols:
    for g in generation_cols:
        corr_matrix.loc[w,g] = df[w].corr(df[g])

corr_matrix = corr_matrix.astype(float)

# -----------------------------
# HEATMAP OVERALL
# -----------------------------

fig = px.imshow(
    corr_matrix,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    aspect="auto"
)

fig.update_layout(
    title="Influence of Weather on Electricity Generation (Germany 2022-2025)",
    xaxis_title="Electricity Generation Type",
    yaxis_title="Weather Condition"
)

fig.write_image("correlation_overall.png")
fig.show()

# -----------------------------
# YEAR BY YEAR HEATMAP
# -----------------------------

years = sorted(df["year"].unique())

fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=[f"Year {y}" for y in years]
)

for idx,year in enumerate(years):

    df_year = df[df["year"]==year]

    corr_year = pd.DataFrame(index=weather_cols, columns=generation_cols)

    for w in weather_cols:
        for g in generation_cols:
            corr_year.loc[w,g] = df_year[w].corr(df_year[g])

    corr_year = corr_year.astype(float)

    row = idx//2 + 1
    col = idx%2 + 1

    fig.add_trace(
        go.Heatmap(
            z=corr_year.values,
            x=corr_year.columns,
            y=corr_year.index,
            colorscale="RdBu",
            zmin=-1,
            zmax=1,
            text=np.round(corr_year.values,2),
            texttemplate="%{text}"
        ),
        row=row,
        col=col
    )

fig.update_layout(height=800,width=1000,title="Weather → Electricity Correlation by Year")
fig.write_image("correlation_by_year.png")
fig.show()
# -----------------------------
# COMBINED DASHBOARD
# WIND OR SOLAR VIA DROPDOWN
# -----------------------------

fig = make_subplots(specs=[[{"secondary_y": True}]])

has_sunshine = "sunshine_duration_h" in df.columns

fig.add_trace(
    go.Scatter(x=df["date"], y=df["wind_onshore"], mode="lines", name="Wind Onshore", visible=True),
    secondary_y=False
)

fig.add_trace(
    go.Scatter(x=df["date"], y=df["wind_offshore"], mode="lines", name="Wind Offshore", visible=True),
    secondary_y=False
)

fig.add_trace(
    go.Scatter(x=df["date"], y=df["wind_max_kmh"], mode="lines", name="Wind Speed", visible=True),
    secondary_y=True
)

fig.add_trace(
    go.Scatter(x=df["date"], y=df["solar"], mode="lines", name="Solar Generation", visible=False),
    secondary_y=False
)

fig.add_trace(
    go.Scatter(x=df["date"], y=df["temp_max_c"], mode="lines", name="Temperature", visible=False),
    secondary_y=True
)

if has_sunshine:
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["sunshine_duration_h"], mode="lines", name="Sunshine Duration", visible=False),
        secondary_y=True
    )

if has_sunshine:
    wind_visible = [True, True, True, False, False, False]
    solar_visible = [False, False, False, True, True, True]
else:
    wind_visible = [True, True, True, False, False]
    solar_visible = [False, False, False, True, True]

fig.update_layout(
    title={"text": "Wind Generation and Wind Speed (Germany 2022–2025)"},
    width=1400,
    height=520,
    hovermode="x unified",
    legend=dict(
        orientation="h",
        y=1.02,
        x=0
    ),
    xaxis=dict(
        title="Date",
        rangeslider=dict(visible=True),
    ),
    yaxis=dict(
        title=dict(text="Wind Generation (MWh)"),
        side="left"
    ),
    yaxis2=dict(
        title=dict(text="Wind Speed (km/h)"),
        overlaying="y",
        side="right"
    ),
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            x=1.02,
            y=1.15,
            xanchor="left",
            yanchor="top",
            buttons=[
                dict(
                    label="Wind Generation",
                    method="update",
                    args=[
                        {"visible": wind_visible},
                        {
                            "title": {"text": "Wind Generation and Wind Speed (Germany 2022–2025)"},
                            "yaxis": {
                                "title": {"text": "Wind Generation (MWh)"},
                                "side": "left"
                            },
                            "yaxis2": {
                                "title": {"text": "Wind Speed (km/h)"},
                                "overlaying": "y",
                                "side": "right"
                            }
                        }
                    ]
                ),
                dict(
                    label="Solar Generation",
                    method="update",
                    args=[
                        {"visible": solar_visible},
                        {
                            "title": {"text": "Solar Generation and Temperature/Sunshine Duration (Germany 2022–2025)"},
                            "yaxis": {
                                "title": {"text": "Solar Generation (MWh)"},
                                "side": "left"
                            },
                            "yaxis2": {
                                "title": {"text": "Weather Values"},
                                "overlaying": "y",
                                "side": "right"
                            }
                        }
                    ]
                )
            ]
        )
    ]
)

fig.write_html("weather_generation_dashboard.html")
fig.show()

# FIGURE 3
# SCATTER: SOLAR vs SUNSHINE
# -----------------------------

if "sunshine_duration_h" in df.columns:
    r_solar = df["sunshine_duration_h"].corr(df["solar"])

    fig = px.scatter(
        df,
        x="sunshine_duration_h",
        y="solar",
        color="year",
        trendline="ols",
        title="Solar Generation vs Sunshine Duration (Germany 2022–2025)",
        labels={
            "sunshine_duration_h": "Sunshine Duration (hours)",
            "solar": "Solar Generation (MWh)",
            "year": "Year"
        },
        opacity=0.65
    )

    fig.update_layout(
        width=900,
        height=550,
        title_subtitle_text=f"Pearson correlation: r = {r_solar:.2f}"
    )

    fig.write_html("scatter_solar_sunshine.html")
    fig.show()

# -----------------------------
# FIGURE 3 + 4 COMBINED
# SCATTER VIA DROPDOWN
# -----------------------------

fig_solar = None
solar_trace_count = 0

if "sunshine_duration_h" in df.columns:
    r_solar = df["sunshine_duration_h"].corr(df["solar"])

    fig_solar = px.scatter(
        df,
        x="sunshine_duration_h",
        y="solar",
        color="year",
        trendline="ols",
        title="Solar Generation vs Sunshine Duration (Germany 2022–2025)",
        labels={
            "sunshine_duration_h": "Sunshine Duration (hours)",
            "solar": "Solar Generation (MWh)",
            "year": "Year"
        },
        opacity=0.65
    )

    fig_solar.update_layout(
        width=900,
        height=550,
        title_subtitle_text=f"Pearson correlation: r = {r_solar:.2f}"
    )

    solar_trace_count = len(fig_solar.data)

r_wind = df["wind_max_kmh"].corr(df["wind_onshore"])

fig_wind = px.scatter(
    df,
    x="wind_max_kmh",
    y="wind_onshore",
    color="year",
    trendline="ols",
    title="Wind Onshore Generation vs Wind Speed (Germany 2022–2025)",
    labels={
        "wind_max_kmh": "Wind Speed (km/h)",
        "wind_onshore": "Wind Onshore Generation (MWh)",
        "year": "Year"
    },
    opacity=0.65
)

fig_wind.update_layout(
    width=900,
    height=550,
    title_subtitle_text=f"Pearson correlation: r = {r_wind:.2f}"
)

wind_trace_count = len(fig_wind.data)

fig = go.Figure()

if fig_solar is not None:
    for tr in fig_solar.data:
        tr.visible = True
        fig.add_trace(tr)

for tr in fig_wind.data:
    tr.visible = False if fig_solar is not None else True
    fig.add_trace(tr)

if fig_solar is not None:
    solar_visible = [True] * solar_trace_count + [False] * wind_trace_count
    wind_visible = [False] * solar_trace_count + [True] * wind_trace_count
else:
    wind_visible = [True] * wind_trace_count

buttons = []

if fig_solar is not None:
    buttons.append(
        dict(
            label="Solar",
            method="update",
            args=[
                {"visible": solar_visible},
                {
                    "title": {
                        "text": "Solar Generation vs Sunshine Duration (Germany 2022–2025)",
                        "subtitle": {"text": f"Pearson correlation: r = {r_solar:.2f}"}
                    },
                    "xaxis": {"title": {"text": "Sunshine Duration (hours)"}},
                    "yaxis": {"title": {"text": "Solar Generation (MWh)"}}
                }
            ]
        )
    )

buttons.append(
    dict(
        label="Wind",
        method="update",
        args=[
            {"visible": wind_visible},
            {
                "title": {
                    "text": "Wind Onshore Generation vs Wind Speed (Germany 2022–2025)",
                    "subtitle": {"text": f"Pearson correlation: r = {r_wind:.2f}"}
                },
                "xaxis": {"title": {"text": "Wind Speed (km/h)"}},
                "yaxis": {"title": {"text": "Wind Onshore Generation (MWh)"}}
            }
        ]
    )
)

if fig_solar is not None:
    fig.update_layout(
        title={
            "text": "Solar Generation vs Sunshine Duration (Germany 2022–2025)",
            "subtitle": {"text": f"Pearson correlation: r = {r_solar:.2f}"}
        },
        xaxis={"title": {"text": "Sunshine Duration (hours)"}},
        yaxis={"title": {"text": "Solar Generation (MWh)"}}
    )
else:
    fig.update_layout(
        title={
            "text": "Wind Onshore Generation vs Wind Speed (Germany 2022–2025)",
            "subtitle": {"text": f"Pearson correlation: r = {r_wind:.2f}"}
        },
        xaxis={"title": {"text": "Wind Speed (km/h)"}},
        yaxis={"title": {"text": "Wind Onshore Generation (MWh)"}}
    )

fig.update_layout(
    width=900,
    height=550,
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            x=1.02,
            y=1.15,
            xanchor="left",
            yanchor="top",
            buttons=buttons
        )
    ]
)

fig.write_html("scatter_dashboard.html")
fig.show()

print("\n✓ All visualizations saved!")