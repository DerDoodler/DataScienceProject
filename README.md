# Weather, Holidays, and Electricity Dynamics in Germany

This project analyzes how weather conditions, public holidays, and regional structures influence electricity consumption, electricity generation, and electricity prices in Germany between 2022 and 2025.

## Main Research Question

**To what extent do weather conditions and public holidays influence electricity consumption and electricity generation in Germany?**

## Sub-Research Questions

### 1. Public Holidays & Electricity Consumption (Germany-wide)
Do public holidays and school holidays in Germany show a measurable difference in daily electricity consumption compared to regular working days when analyzing Germany as a whole?

### 2. Seasonal Patterns in Electricity Consumption
How does electricity consumption vary across seasons in Germany, and how does this relate to seasonal weather conditions?

### 3. Weather Influence on Renewable Generation
How strongly do weather conditions (especially wind speed and sunshine / solar radiation) explain daily electricity generation from wind and photovoltaic (PV) in Germany?

### 4. Generation Mix during High Renewable Output
How does Germany’s electricity generation mix change on days with high renewable output (wind and PV), and which conventional sources (lignite, hard coal, gas) decrease the most?

### 5. Regional Differences in Electricity Consumption
How does electricity consumption differ between Germany’s TSO control areas (50Hertz, Amprion, TenneT, TransnetBW), and which factors may explain these regional differences?

### 6. Correlation between Electricity Consumption and Generation in TSO Regions
To what extent is electricity consumption correlated with electricity generation within Germany’s TSO control areas, and are there observable relationships between regional demand and regional electricity production?

### 7. Renewable Generation and Electricity Prices
How are electricity prices related to renewable electricity generation levels, and do high renewable generation periods correspond to lower electricity prices in Germany?

## Project Overview

This project combines energy market data, weather data, and holiday information to examine Germany-wide and regional electricity patterns. The analysis is based on public electricity and market data, historical weather data, and holiday calendars.

The regional analysis focuses on the four German TSO control areas:

- 50Hertz
- Amprion
- TenneT
- TransnetBW

This is important because electricity data in Germany is structured by transmission system zones rather than by political regions such as federal states or cities.

## Data Sources

The project uses the following data sources:

- **[SMARD API](https://www.smard.de/en)** for electricity generation, electricity consumption, and electricity price data
- **[Open-Meteo API](https://open-meteo.com/)** for historical weather data
- **[OpenHolidays API](https://www.openholidaysapi.org/en/)** for public holidays and school holidays in Germany


### Main Variables

Examples of variables used in this project include:

- electricity consumption / net load
- electricity generation by source type
- renewable generation from wind onshore, wind offshore, and photovoltaics
- electricity prices
- wind speed
- sunshine duration / solar-related weather indicators
- temperature
- precipitation
- public holidays and school holidays
- date and TSO region

### Time Period

The project covers the period **2022 to 2025**.

## Data Pipeline

The project follows a structured workflow from raw data collection to final website presentation.

### 1. Data Collection
Data was fetched from public APIs and additional holiday sources, then stored locally for further processing.

### 2. Data Cleaning and Preprocessing
The raw data was cleaned and standardized before analysis. This included:
- converting timestamps into a consistent datetime format,
- normalizing time zones,
- selecting relevant categories and variables,
- and handling missing or inconsistent values where necessary.

### 3. Temporal Harmonization
Because the original datasets came in different time resolutions such as quarter-hourly, hourly, and daily values, all relevant datasets were converted to a **common daily level** so they could be compared consistently.

### 4. Data Merging
The processed datasets were merged by **date** and, where needed, by **TSO zone**, resulting in analysis-ready datasets for the individual research questions.

### 5. Variable Selection
Since electricity generation consists of multiple source types, relevant generation categories first had to be identified from the available API filters. Depending on the research question, the appropriate source types were selected.

For the renewable generation analysis, the project focused especially on:
- Wind Onshore
- Wind Offshore
- Photovoltaics (PV)

These were matched with suitable weather variables:
- wind speed for wind generation,
- sunshine duration for PV generation.

### 6. Analysis and Visualization
The project uses descriptive statistics, correlation analysis, and visualizations such as scatterplots, line charts, bar charts, and boxplots.

The visualizations were created in Python and exported as **HTML files**. These exported HTML visualizations were then integrated into the website.

## Project Files

The repository contains the Python scripts used for data collection, preprocessing, analysis, and visualization, as well as the website files used to present the results.

Depending on the project structure, the repository may include:

- Python scripts for fetching and processing API data
- analysis scripts for the individual research questions
- exported visualization files in HTML format
- website files such as HTML, CSS, and JavaScript
- documentation files such as this README

The exact file and folder structure may vary depending on the final project version.

## Website

### How the Website Was Built

The website was built as the presentation layer of the project. The data analysis was carried out in Python, while the results were presented through a website combining explanatory text and embedded visualizations.

The charts were generated in Python and exported as **HTML files**. These exported files were then integrated into the website so that users could interact with the visualizations directly in the browser.

### How the Data Is Connected

The website does not rely on live API calls in the browser. Instead, the workflow is:

1. data is collected and processed in Python,
2. visualizations are created from the processed data,
3. these visualizations are exported as HTML files,
4. and the exported files are embedded into the website.

This means the website is connected to the processed outputs of the analysis pipeline rather than directly querying external APIs at runtime.

### Deployment with GitHub Pages

The website was deployed using **GitHub Pages**, which allows static websites to be hosted directly from a GitHub repository.

The deployment works as follows:

1. the website files, including `index.html`, CSS, JavaScript, and exported HTML visualizations, are stored in the repository,
2. GitHub Pages publishes these files as a static website,
3. when changes are pushed to the selected branch or deployment folder, the website can be updated automatically.

This makes GitHub Pages a practical solution for projects that are based on static files and pre-generated visualizations.

### Project Links

- **Live website:** `https://waledoc.github.io/DataScienceProject/index.html`
- **Repository:** `https://github.com/Waledoc/DataScienceProject`

## How to Use the Web Application

The website is organized around the main research question and the seven sub-research questions. Users can navigate through the sections, read the research focus and results, and explore the visualizations.

### Highlights

Main features of the web application include:
- analysis of holiday and school holiday effects on electricity consumption,
- seasonal electricity consumption patterns,
- renewable generation and weather relationships,
- generation mix changes during high renewable output,
- regional comparisons across the four TSO control areas,
- regional relationships between electricity generation and consumption,
- and the relationship between renewable generation and electricity prices.

Because the charts are embedded as HTML visualizations, users can interact with them directly in the browser, for example by hovering, zooming, or filtering where available.

## Technologies Used

This project uses the following technologies:

- Python
- Pandas
- Plotly
- HTML
- CSS
- JavaScript
- JSON-based API data
- GitHub Pages

## Code Quality and Documentation

The code is part of the project assessment. Therefore, the project aims to follow good coding practice, including:

- **PEP 8** style guidelines
- principles of the **Zen of Python**
- clear naming conventions
- readable structure
- comments for easy comprehensibility

The **README** together with the **code comments** serves as the documentation of the project.

## Marking of LLM-Supported Code

According to the project requirements, all code that was directly generated by an LLM or developed with substantial LLM support was marked in the repository.

The marking was handled as follows:

- **API and data processing scripts:**  
  Individual sections that were generated or substantially supported by an LLM were marked directly with comments at the relevant code sections.

- **Visualization scripts:**  
  Since large parts of the visualization code were either generated by an LLM or revised with LLM support, these files contain a general comment at the top of the file indicating LLM involvement.

- **HTML files of the website:**  
  The HTML structure was largely repetitive across pages. Therefore, explicit LLM comments were added to `index.html` and `rq1.html` as representative files, while the remaining HTML pages follow the same structural approach.

All LLM-supported code was reviewed, adapted, and tested manually before being included in the final version of the project.
