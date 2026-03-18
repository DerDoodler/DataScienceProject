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

region = "DE"

renewable_types = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV",
    "Generation: Hydropower",
    "Generation: Biomass",
    "Generation: Other Renewables"
]

price_name = "Market price: DE/LU"

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

all_records = []

for file in smard_files:
    if not os.path.exists(file):
        print(f"✗ File not found: {file}")
        continue

    with open(file, "r", encoding="utf-8") as f:
        smard = json.load(f)

    if region in smard["regions"]:
        df_temp = pd.DataFrame(smard["regions"][region])
        all_records.append(df_temp)

    print(f"✓ Loaded {file}")

df = pd.concat(all_records, ignore_index=True)

df["date"] = (
    pd.to_datetime(df["date"], utc=True)
    .dt.tz_convert(TZ)
    .dt.normalize()
    .dt.tz_localize(None)
)

# --------------------------------------------------
# BUILD DAILY PRICE + RENEWABLE GENERATION DATASET
# --------------------------------------------------

df_price = (
    df[df["name"] == price_name]
    .groupby("date", as_index=False)["value"]
    .mean()
    .rename(columns={"value": "price_eur_mwh"})
)

df_renew = (
    df[df["name"].isin(renewable_types)]
    .groupby("date", as_index=False)["value"]
    .sum()
    .rename(columns={"value": "renewable_generation_mwh"})
)

df_renew_detail = (
    df[df["name"].isin(renewable_types)]
    .pivot_table(index="date", columns="name", values="value", aggfunc="mean")
    .reset_index()
)

merged = pd.merge(df_price, df_renew, on="date", how="inner")
merged = pd.merge(merged, df_renew_detail, on="date", how="left")

merged["year"] = merged["date"].dt.year
merged["month"] = merged["date"].dt.month

r_total = merged["renewable_generation_mwh"].corr(merged["price_eur_mwh"])

print("\nOverall correlation:")
print(f"Renewables vs price: r = {r_total:.3f}")

# --------------------------------------------------
# 1. SCATTER: RENEWABLES VS PRICE
# --------------------------------------------------

fig_scatter = px.scatter(
    merged,
    x="renewable_generation_mwh",
    y="price_eur_mwh",
    color="year",
    trendline="ols",
    title="Electricity Prices vs Renewable Generation in Germany (2022–2025)",
    labels={
        "renewable_generation_mwh": "Renewable Generation (MWh)",
        "price_eur_mwh": "Electricity Price (€/MWh)",
        "year": "Year"
    },
    opacity=0.6
)

year_corrs = []
for year in sorted(merged["year"].unique()):
    d = merged[merged["year"] == year].dropna(subset=["renewable_generation_mwh", "price_eur_mwh"])
    if len(d) >= 2:
        r = d["renewable_generation_mwh"].corr(d["price_eur_mwh"])
        year_corrs.append(f"{year}: r = {r:.2f}")

corr_text = "<br>".join(year_corrs)

fig_scatter.update_layout(
    title=dict(
        text="Electricity Prices vs Renewable Generation in Germany (2022–2025)",
        subtitle=dict(
            text=f"Overall correlation: r = {r_total:.2f}",
            font=dict(size=14)
        ),
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    font=dict(size=15),
    xaxis=dict(
        title=dict(text="Renewable Generation (MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    yaxis=dict(
        title=dict(text="Electricity Price (€/MWh)", font=dict(size=18)),
        tickfont=dict(size=15)
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    ),
    margin=dict(r=220)
)

fig_scatter.add_annotation(
    x=1.02,
    y=0.78,
    xref="paper",
    yref="paper",
    text="<b>Correlations by year</b><br>" + corr_text,
    showarrow=False,
    align="left",
    xanchor="left",
    yanchor="top",
    bordercolor="gray",
    borderwidth=1,
    bgcolor="white",
    font=dict(size=14)
)

fig_scatter.write_html("renewables_vs_price_scatter.html", auto_open=True)

# --------------------------------------------------
# 2. TIME SERIES: PRICE + RENEWABLES
# --------------------------------------------------

fig_ts = go.Figure()

fig_ts.add_trace(
    go.Scatter(
        x=merged["date"],
        y=merged["renewable_generation_mwh"],
        mode="lines",
        name="Renewable Generation",
        yaxis="y1"
    )
)

fig_ts.add_trace(
    go.Scatter(
        x=merged["date"],
        y=merged["price_eur_mwh"],
        mode="lines",
        name="Electricity Price",
        yaxis="y2"
    )
)

fig_ts.update_layout(
    title=dict(
        text="Renewable Generation and Electricity Prices Over Time (Germany 2022–2025)",
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
        title=dict(text="Renewable Generation (MWh)", font=dict(size=18)),
        tickfont=dict(size=15),
        side="left"
    ),
    yaxis2=dict(
        title=dict(text="Electricity Price (€/MWh)", font=dict(size=18)),
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

fig_ts.write_html("renewables_vs_price_timeseries.html", auto_open=True)

# --------------------------------------------------
# 3. QUANTILE COMPARISON:
# LOW vs HIGH RENEWABLE PERIODS
# --------------------------------------------------

q_low = merged["renewable_generation_mwh"].quantile(0.25)
q_high = merged["renewable_generation_mwh"].quantile(0.75)

merged["renewable_period"] = "Medium"

merged.loc[merged["renewable_generation_mwh"] <= q_low, "renewable_period"] = "Low renewable"
merged.loc[merged["renewable_generation_mwh"] >= q_high, "renewable_period"] = "High renewable"

compare = (
    merged[merged["renewable_period"] != "Medium"]
    .groupby("renewable_period", as_index=False)["price_eur_mwh"]
    .mean()
)

fig_compare = px.bar(
    compare,
    x="renewable_period",
    y="price_eur_mwh",
    color="renewable_period",
    title="Average Electricity Price in Low vs High Renewable Generation Periods",
    labels={
        "renewable_period": "Renewable Generation Period",
        "price_eur_mwh": "Average Electricity Price (€/MWh)"
    },
    text_auto=".2f"
)

fig_compare.update_layout(
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

fig_compare.update_traces(textfont=dict(size=15))

fig_compare.write_html("renewables_price_quantile_compare.html", auto_open=True)

# --------------------------------------------------
# 4. MONTHLY PATTERN
# --------------------------------------------------

monthly = (
    merged.groupby(["year", "month"], as_index=False)[["renewable_generation_mwh", "price_eur_mwh"]]
    .mean()
)

fig_month = go.Figure()

for year in sorted(monthly["year"].unique()):
    d = monthly[monthly["year"] == year]

    fig_month.add_trace(
        go.Scatter(
            x=d["month"],
            y=d["renewable_generation_mwh"],
            mode="lines+markers",
            name=f"{year} Renewables",
            yaxis="y1"
        )
    )

    fig_month.add_trace(
        go.Scatter(
            x=d["month"],
            y=d["price_eur_mwh"],
            mode="lines+markers",
            name=f"{year} Price",
            yaxis="y2"
        )
    )

fig_month.update_layout(
    title=dict(
        text="Monthly Renewable Generation and Electricity Prices (Germany 2022–2025)",
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
        title=dict(text="Renewable Generation (MWh)", font=dict(size=18)),
        tickfont=dict(size=15),
        side="left"
    ),
    yaxis2=dict(
        title=dict(text="Electricity Price (€/MWh)", font=dict(size=18)),
        tickfont=dict(size=15),
        overlaying="y",
        side="right"
    ),
    legend=dict(
        font=dict(size=15),
        title=dict(font=dict(size=16))
    )
)

fig_month.write_html("renewables_vs_price_monthly.html", auto_open=True)

# --------------------------------------------------
# 5. OPTIONAL: COMPONENT-LEVEL CORRELATIONS
# --------------------------------------------------

component_cols = [
    "Generation: Wind Onshore",
    "Generation: Wind Offshore",
    "Generation: PV",
    "Generation: Hydropower",
    "Generation: Biomass",
    "Generation: Other Renewables"
]

component_corr = []

for col in component_cols:
    if col in merged.columns:
        r = merged[col].corr(merged["price_eur_mwh"])
        component_corr.append({
            "renewable_source": col.replace("Generation: ", ""),
            "correlation_with_price": r
        })

corr_df = pd.DataFrame(component_corr).sort_values("correlation_with_price")

fig_corr = px.bar(
    corr_df,
    x="renewable_source",
    y="correlation_with_price",
    color="correlation_with_price",
    title="Correlation of Renewable Generation Components with Electricity Price",
    labels={
        "renewable_source": "Renewable Source",
        "correlation_with_price": "Correlation with Price"
    },
    text_auto=".2f",
    color_continuous_scale="RdBu_r"
)

fig_corr.update_layout(
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
    coloraxis_colorbar=dict(
        tickfont=dict(size=14),
        title=dict(font=dict(size=16))
    )
)

fig_corr.update_traces(textfont=dict(size=15))
fig_corr.update_layout(coloraxis_showscale=False)

fig_corr.write_html("renewable_components_price_correlation.html", auto_open=True)

# --------------------------------------------------
# CONSOLE OUTPUT
# --------------------------------------------------

print("\nAverage prices by renewable period:")
print(compare)

print("\nCorrelation by component:")
print(corr_df.round(3))

print("\n✓ HTML files created:")
print(" - renewables_vs_price_scatter.html")
print(" - renewables_vs_price_timeseries.html")
print(" - renewables_price_quantile_compare.html")
print(" - renewables_vs_price_monthly.html")
print(" - renewable_components_price_correlation.html")
