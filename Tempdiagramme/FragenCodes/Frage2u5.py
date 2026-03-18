import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TZ = "Europe/Berlin"

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

smard_files = [
    "smard_data_2022.json",
    "smard_data_2023.json",
    "smard_data_2024.json",
    "smard_data_2025.json"
]

weather_file = "weather_data22-25.json"
tsos = ["50Hertz", "Amprion", "TenneT", "TransnetBW"]
target_name = "Consumption: Total (Net load)"

# --------------------------------------------------
# LOAD POWER DATA
# --------------------------------------------------

all_power = {tso: [] for tso in tsos}

for file in smard_files:
    if not os.path.exists(file):
        print(f"✗ File not found: {file}")
        continue

    with open(file, "r", encoding="utf-8") as f:
        smard = json.load(f)

    for tso in tsos:
        if tso in smard["regions"]:
            df_temp = pd.DataFrame(smard["regions"][tso])
            all_power[tso].append(df_temp)

    print(f"✓ Loaded {file}")

dfs_power = {}

for tso in tsos:
    if not all_power[tso]:
        continue

    df_tso = pd.concat(all_power[tso], ignore_index=True)
    df_tso["date"] = (
        pd.to_datetime(df_tso["date"], utc=True)
        .dt.tz_convert(TZ)
        .dt.normalize()
        .dt.tz_localize(None)
    )

    df_tso = df_tso[df_tso["name"] == target_name].copy()
    df_tso = df_tso[["date", "value"]]
    df_tso.rename(columns={"value": "consumption_mwh"}, inplace=True)
    df_tso["tso"] = tso
    df_tso["year"] = df_tso["date"].dt.year
    df_tso["month"] = df_tso["date"].dt.month
    df_tso["weekday"] = df_tso["date"].dt.day_name()

    dfs_power[tso] = df_tso

df = pd.concat(dfs_power.values(), ignore_index=True)

print("\nLoaded TSO consumption data:")
print(df.groupby("tso")["consumption_mwh"].agg(["count", "mean"]).round(2))

# --------------------------------------------------
# LOAD OPTIONAL WEATHER DATA
# --------------------------------------------------

df_weather = None

if os.path.exists(weather_file):
    with open(weather_file, "r", encoding="utf-8") as f:
        weather = json.load(f)

    weather_parts = []

    for tso in tsos:
        if tso in weather["regions"]:
            d = pd.DataFrame(weather["regions"][tso])
            d["date"] = (
                pd.to_datetime(d["date"], utc=True)
                .dt.tz_convert(TZ)
                .dt.normalize()
                .dt.tz_localize(None)
            )
            d["tso"] = tso
            weather_parts.append(d)

    if weather_parts:
        df_weather = pd.concat(weather_parts, ignore_index=True)
        print(f"✓ Loaded {weather_file}")

# --------------------------------------------------
# 1. AVERAGE CONSUMPTION BY TSO
# --------------------------------------------------

avg_tso = (
    df.groupby("tso", as_index=False)["consumption_mwh"]
    .mean()
    .sort_values("consumption_mwh", ascending=False)
)

fig_avg = px.bar(
    avg_tso,
    x="tso",
    y="consumption_mwh",
    color="tso",
    title="Average Electricity Consumption by TSO Control Area (2022–2025)",
    labels={
        "tso": "TSO Control Area",
        "consumption_mwh": "Average Daily Consumption (MWh)"
    },
    text_auto=".0f"
)

fig_avg.update_layout(
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

fig_avg.update_traces(textfont=dict(size=15))

fig_avg.write_html("regional_consumption_avg.html", auto_open=True)

# --------------------------------------------------
# 2. TIME SERIES BY TSO
# --------------------------------------------------

fig_ts = px.line(
    df,
    x="date",
    y="consumption_mwh",
    color="tso",
    title="Daily Electricity Consumption by TSO Control Area (2022–2025)",
    labels={
        "date": "Date",
        "consumption_mwh": "Daily Consumption (MWh)",
        "tso": "TSO"
    }
)

fig_ts.update_layout(
    title=dict(
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=18)),
        tickfont=dict(size=15),
        rangeslider=dict(visible=True)
    ),
    yaxis=dict(
        title=dict(text="Daily Consumption (MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    ),
    hovermode="x unified"
)

fig_ts.write_html("regional_consumption_timeseries.html", auto_open=True)

# --------------------------------------------------
# 3. DISTRIBUTION BY TSO
# --------------------------------------------------

fig_box = px.box(
    df,
    x="tso",
    y="consumption_mwh",
    color="tso",
    title="Distribution of Daily Electricity Consumption by TSO",
    labels={
        "tso": "TSO Control Area",
        "consumption_mwh": "Daily Consumption (MWh)"
    },
    points="outliers"
)

fig_box.update_layout(
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

fig_box.write_html("regional_consumption_boxplot.html", auto_open=True)

# --------------------------------------------------
# 4. MONTHLY SEASONAL PROFILE
# --------------------------------------------------

monthly = (
    df.groupby(["tso", "month"], as_index=False)["consumption_mwh"]
    .mean()
)

fig_month = px.line(
    monthly,
    x="month",
    y="consumption_mwh",
    color="tso",
    markers=True,
    title="Average Monthly Electricity Consumption by TSO",
    labels={
        "month": "Month",
        "consumption_mwh": "Average Consumption (MWh)",
        "tso": "TSO"
    }
)

fig_month.update_layout(
    title=dict(
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=18)),
        tickfont=dict(size=15),
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ),
    yaxis=dict(
        title=dict(text="Average Consumption (MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    )
)

fig_month.write_html("regional_consumption_monthly.html", auto_open=True)

# --------------------------------------------------
# 5. WEEKDAY PROFILE
# --------------------------------------------------

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

weekday = (
    df.groupby(["tso", "weekday"], as_index=False)["consumption_mwh"]
    .mean()
)

weekday["weekday"] = pd.Categorical(weekday["weekday"], categories=weekday_order, ordered=True)
weekday = weekday.sort_values(["tso", "weekday"])

fig_weekday = px.line(
    weekday,
    x="weekday",
    y="consumption_mwh",
    color="tso",
    markers=True,
    title="Average Weekday Consumption Pattern by TSO",
    labels={
        "weekday": "Weekday",
        "consumption_mwh": "Average Consumption (MWh)",
        "tso": "TSO"
    }
)

fig_weekday.update_layout(
    title=dict(
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(text="Weekday", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    yaxis=dict(
        title=dict(text="Average Consumption (MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    )
)

fig_weekday.write_html("regional_consumption_weekday.html", auto_open=True)

# --------------------------------------------------
# 6. OPTIONAL: WEATHER VS CONSUMPTION
# --------------------------------------------------

if df_weather is not None:
    possible_cols = [c for c in ["temp_max_c", "wind_max_kmh", "sunshine_duration_h", "precipitation_sum_mm"] if c in df_weather.columns]

    if "sunshine_duration_s" in df_weather.columns and "sunshine_duration_h" not in df_weather.columns:
        df_weather["sunshine_duration_h"] = df_weather["sunshine_duration_s"] / 3600
        possible_cols = [c for c in ["temp_max_c", "wind_max_kmh", "sunshine_duration_h", "precipitation_sum_mm"] if c in df_weather.columns]

    merged = pd.merge(df, df_weather[["date", "tso"] + possible_cols], on=["date", "tso"], how="inner")

    if "temp_max_c" in merged.columns:
        fig_temp = px.scatter(
            merged,
            x="temp_max_c",
            y="consumption_mwh",
            color="tso",
            trendline="ols",
            title="Consumption vs Temperature by TSO",
            labels={
                "temp_max_c": "Maximum Temperature (°C)",
                "consumption_mwh": "Daily Consumption (MWh)",
                "tso": "TSO"
            },
            opacity=0.6
        )

        corr_lines = []

        for tso in sorted(merged["tso"].dropna().unique()):
            d = merged[merged["tso"] == tso].dropna(subset=["temp_max_c", "consumption_mwh"])
            if len(d) >= 2:
                r = d["temp_max_c"].corr(d["consumption_mwh"])
                corr_lines.append(f"{tso}: r = {r:.2f}")

        corr_text = "<br>".join(corr_lines)

        fig_temp.update_layout(
            title=dict(
                x=0.5,
                xanchor="center",
                font=dict(size=24)
            ),
            font=dict(size=15),
            xaxis=dict(
                title=dict(text="Maximum Temperature (°C)", font=dict(size=18)),
                tickfont=dict(size=15)
            ),
            yaxis=dict(
                title=dict(text="Daily Consumption (MWh)", font=dict(size=18)),
                tickfont=dict(size=15)
            ),
            legend=dict(
                font=dict(size=15),
                title=dict(font=dict(size=16))
            ),
            margin=dict(r=220)
        )

        fig_temp.add_annotation(
            x=1.02,
            y=0.78,
            xref="paper",
            yref="paper",
            text="<b>Correlations by TSO</b><br>" + corr_text,
            showarrow=False,
            align="left",
            xanchor="left",
            yanchor="top",
            bordercolor="gray",
            borderwidth=1,
            bgcolor="white",
            font=dict(size=14)
        )

        fig_temp.write_html("regional_consumption_vs_temperature.html", auto_open=True)

    # --------------------------------------------------
    # 6B. GERMANY: SEASONAL CONSUMPTION VS WEATHER
    # --------------------------------------------------

    season_map = {
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn"
    }

    de_merged = merged[merged["tso"] == "DE"].copy() if "DE" in merged["tso"].unique() else None

    if de_merged is None or de_merged.empty:
        de_power = (
            df.groupby("date", as_index=False)["consumption_mwh"]
            .sum()
            .rename(columns={"consumption_mwh": "consumption_mwh"})
        )

        de_weather = (
            df_weather.groupby("date", as_index=False)[possible_cols]
            .mean()
        )

        de_merged = pd.merge(de_power, de_weather, on="date", how="inner")

    de_merged["month"] = de_merged["date"].dt.month
    de_merged["season"] = de_merged["month"].map(season_map)

    season_order = ["Winter", "Spring", "Summer", "Autumn"]
    de_merged["season"] = pd.Categorical(de_merged["season"], categories=season_order, ordered=True)

    seasonal = (
        de_merged.groupby("season", as_index=False)[["consumption_mwh", "temp_max_c"]]
        .mean()
    )

    if "sunshine_duration_h" in de_merged.columns:
        seasonal["sunshine_duration_h"] = (
            de_merged.groupby("season")["sunshine_duration_h"].mean().values
        )

    fig_season = go.Figure()

    fig_season.add_trace(
        go.Bar(
            x=seasonal["season"],
            y=seasonal["consumption_mwh"],
            name="Electricity Consumption",
            yaxis="y1"
        )
    )

    fig_season.add_trace(
        go.Scatter(
            x=seasonal["season"],
            y=seasonal["temp_max_c"],
            mode="lines+markers",
            name="Average Temperature",
            yaxis="y2"
        )
    )

    if "sunshine_duration_h" in seasonal.columns:
        fig_season.add_trace(
            go.Scatter(
                x=seasonal["season"],
                y=seasonal["sunshine_duration_h"],
                mode="lines+markers",
                name="Sunshine Duration",
                yaxis="y2"
            )
        )

    fig_season.update_layout(
        title=dict(
            text="Seasonal Electricity Consumption and Weather in Germany (2022–2025)",
            x=0.5,
            xanchor="center",
            font=dict(size=24)
        ),
        font=dict(size=15),
        xaxis=dict(
            title=dict(text="Season", font=dict(size=18)),
            tickfont=dict(size=15)
        ),
        yaxis=dict(
            title=dict(text="Average Electricity Consumption (MWh)", font=dict(size=18)),
            tickfont=dict(size=15),
            side="left"
        ),
        yaxis2=dict(
            title=dict(text="Weather Values", font=dict(size=18)),
            tickfont=dict(size=15),
            overlaying="y",
            side="right"
        ),
        legend=dict(
            font=dict(size=15),
            title=dict(font=dict(size=16))
        ),
        hovermode="x unified"
    )

    fig_season.write_html("seasonal_consumption_weather_germany.html", auto_open=True)

# --------------------------------------------------
# 7. SIMPLE NUMERIC SUMMARY
# --------------------------------------------------

summary = (
    df.groupby("tso")["consumption_mwh"]
    .agg(["mean", "median", "min", "max", "std"])
    .round(2)
    .sort_values("mean", ascending=False)
)

print("\nRegional consumption summary:")
print(summary)

print("\nPossible explanation factors to discuss:")
print("- TSO areas cover different parts of Germany.")
print("- Industrial concentration differs strongly by region.")
print("- Population and urban structure differ by control area.")
print("- Weather and heating/cooling patterns vary regionally.")
print("- Renewable-heavy northern areas and industrial western/southern areas can show different load profiles.")

print("\n✓ HTML files created:")
print(" - regional_consumption_avg.html")
print(" - regional_consumption_timeseries.html")
print(" - regional_consumption_boxplot.html")
print(" - regional_consumption_monthly.html")
print(" - regional_consumption_weekday.html")
if df_weather is not None:
    print(" - regional_consumption_vs_temperature.html")
