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

tsos = ["50Hertz", "Amprion", "TenneT", "TransnetBW"]

generation_types = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV",
    "Generation: Hydropower",
    "Generation: Biomass",
    "Generation: Lignite",
    "Generation: Nuclear",
    "Generation: Gas",
    "Generation: Hard Coal",
    "Generation: Other Conventional",
    "Generation: Other Renewables",
    "Generation: Pumped Storage"
]

consumption_name = "Consumption: Total (Net load)"

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

all_data = {tso: [] for tso in tsos}

for file in smard_files:
    if not os.path.exists(file):
        print(f"✗ File not found: {file}")
        continue

    with open(file, "r", encoding="utf-8") as f:
        smard = json.load(f)

    for tso in tsos:
        if tso in smard["regions"]:
            df_temp = pd.DataFrame(smard["regions"][tso])
            all_data[tso].append(df_temp)

    print(f"✓ Loaded {file}")

dfs = {}

for tso in tsos:
    if not all_data[tso]:
        continue

    d = pd.concat(all_data[tso], ignore_index=True)

    d["date"] = (
        pd.to_datetime(d["date"], utc=True)
        .dt.tz_convert(TZ)
        .dt.normalize()
        .dt.tz_localize(None)
    )

    dfs[tso] = d

# --------------------------------------------------
# BUILD DAILY CONSUMPTION + GENERATION TABLE
# --------------------------------------------------

merged_parts = []

for tso in tsos:
    if tso not in dfs:
        continue

    d = dfs[tso]

    cons = (
        d[d["name"] == consumption_name]
        .groupby("date", as_index=False)["value"]
        .mean()
        .rename(columns={"value": "consumption_mwh"})
    )

    gen = (
        d[d["name"].isin(generation_types)]
        .groupby("date", as_index=False)["value"]
        .sum()
        .rename(columns={"value": "generation_mwh"})
    )

    both = pd.merge(cons, gen, on="date", how="inner")
    both["tso"] = tso
    both["year"] = both["date"].dt.year
    both["month"] = both["date"].dt.month

    merged_parts.append(both)

df = pd.concat(merged_parts, ignore_index=True)

print("\nDaily merged dataset:")
print(df.head())

# --------------------------------------------------
# 1. SCATTER: GENERATION VS CONSUMPTION
# --------------------------------------------------

fig_scatter = px.scatter(
    df,
    x="generation_mwh",
    y="consumption_mwh",
    color="tso",
    trendline="ols",
    title="Electricity Consumption vs Generation in Germany's TSO Regions (2022–2025)",
    labels={
        "generation_mwh": "Regional Electricity Generation (MWh)",
        "consumption_mwh": "Regional Electricity Consumption (MWh)",
        "tso": "TSO Region"
    },
    opacity=0.6
)

corr_lines = []
for tso in sorted(df["tso"].unique()):
    d = df[df["tso"] == tso].dropna(subset=["generation_mwh", "consumption_mwh"])
    if len(d) >= 2:
        r = d["generation_mwh"].corr(d["consumption_mwh"])
        corr_lines.append(f"{tso}: r = {r:.2f}")

corr_text = "<br>".join(corr_lines)

fig_scatter.update_layout(
    title=dict(
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(text="Regional Electricity Generation (MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    yaxis=dict(
        title=dict(text="Regional Electricity Consumption (MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    ),
    margin=dict(r=240)
)

fig_scatter.add_annotation(
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

fig_scatter.write_html("tso_consumption_vs_generation_scatter.html", auto_open=True)

# --------------------------------------------------
# 2. TIME SERIES: GENERATION AND CONSUMPTION
# --------------------------------------------------

fig_ts = go.Figure()

default_tso = "50Hertz"
visible_map = {}

for tso in tsos:
    d = df[df["tso"] == tso].sort_values("date")
    visible_map[tso] = [False] * (2 * len(tsos))

for i, tso in enumerate(tsos):
    d = df[df["tso"] == tso].sort_values("date")

    fig_ts.add_trace(
        go.Scatter(
            x=d["date"],
            y=d["consumption_mwh"],
            mode="lines",
            name=f"{tso} Consumption",
            visible=(tso == default_tso)
        )
    )

    fig_ts.add_trace(
        go.Scatter(
            x=d["date"],
            y=d["generation_mwh"],
            mode="lines",
            name=f"{tso} Generation",
            visible=(tso == default_tso)
        )
    )

for i, tso in enumerate(tsos):
    visible = [False] * (2 * len(tsos))
    visible[2 * i] = True
    visible[2 * i + 1] = True
    visible_map[tso] = visible

buttons = []
for tso in tsos:
    buttons.append(
        dict(
            label=tso,
            method="update",
            args=[
                {"visible": visible_map[tso]},
                {
                    "title": {
                        "text": f"Consumption and Generation Over Time — {tso} (2022–2025)",
                        "x": 0.5,
                        "xanchor": "center",
                        "font": {"size": 24}
                    }
                }
            ]
        )
    )

fig_ts.update_layout(
    title=dict(
        text=f"Consumption and Generation Over Time — {default_tso} (2022–2025)",
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
        title=dict(text="MWh", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    ),
    hovermode="x unified",
    updatemenus=[
        dict(
            buttons=buttons,
            direction="down",
            showactive=True,
            x=0.02,
            y=1.15,
            xanchor="left",
            yanchor="top",
            font=dict(size=15)
        )
    ]
)

fig_ts.write_html("tso_consumption_generation_timeseries.html", auto_open=True)

# --------------------------------------------------
# 3. RATIO: GENERATION / CONSUMPTION
# --------------------------------------------------

df["gen_to_cons_ratio"] = df["generation_mwh"] / df["consumption_mwh"]

fig_ratio = px.box(
    df,
    x="tso",
    y="gen_to_cons_ratio",
    color="tso",
    title="Distribution of Generation-to-Consumption Ratios by TSO",
    labels={
        "tso": "TSO Region",
        "gen_to_cons_ratio": "Generation / Consumption Ratio"
    },
    points="outliers"
)

fig_ratio.update_layout(
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

fig_ratio.write_html("tso_generation_consumption_ratio.html", auto_open=True)

# --------------------------------------------------
# 4. MONTHLY PATTERN
# --------------------------------------------------

monthly = (
    df.groupby(["tso", "month"], as_index=False)[["generation_mwh", "consumption_mwh"]]
    .mean()
)

fig_month = go.Figure()

for tso in tsos:
    d = monthly[monthly["tso"] == tso]

    fig_month.add_trace(
        go.Scatter(
            x=d["month"],
            y=d["consumption_mwh"],
            mode="lines+markers",
            name=f"{tso} Consumption"
        )
    )

    fig_month.add_trace(
        go.Scatter(
            x=d["month"],
            y=d["generation_mwh"],
            mode="lines+markers",
            name=f"{tso} Generation"
        )
    )

fig_month.update_layout(
    title=dict(
        text="Monthly Average Consumption and Generation by TSO (2022–2025)",
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
        title=dict(text="Average MWh", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    )
)

fig_month.write_html("tso_monthly_generation_consumption.html", auto_open=True)

# --------------------------------------------------
# 5. SUMMARY TABLE IN CONSOLE
# --------------------------------------------------

summary = (
    df.groupby("tso")
    .apply(lambda x: pd.Series({
        "correlation": x["generation_mwh"].corr(x["consumption_mwh"]),
        "avg_consumption_mwh": x["consumption_mwh"].mean(),
        "avg_generation_mwh": x["generation_mwh"].mean(),
        "avg_ratio": (x["generation_mwh"] / x["consumption_mwh"]).mean()
    }))
    .round(3)
    .sort_values("correlation", ascending=False)
)

print("\nCorrelation between regional consumption and regional generation:")
print(summary)

print("\n✓ HTML files created:")
print(" - tso_consumption_vs_generation_scatter.html")
print(" - tso_consumption_generation_timeseries.html")
print(" - tso_generation_consumption_ratio.html")
print(" - tso_monthly_generation_consumption.html")
