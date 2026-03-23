# Weather, Holidays, and Electricity Dynamics in Germany

This project analyzes how weather conditions, public holidays, and regional structures influence electricity consumption, electricity generation, and electricity prices in Germany between 2022 and 2025.

## Main Research Question

**To what extent do weather conditions and public holidays influence electricity consumption and electricity generation in Germany?**

## Sub-Research Questions

1. **Public Holidays & Electricity Consumption (Germany-wide)**  
   Do public holidays and school holidays in Germany show a measurable difference in daily electricity consumption compared to regular working days when analyzing Germany as a whole?

2. **Seasonal Patterns in Electricity Consumption**  
   How does electricity consumption vary across seasons in Germany, and how does this relate to seasonal weather conditions?

3. **Weather Influence on Renewable Generation**  
   How strongly do weather conditions (especially wind speed and sunshine / solar radiation) explain daily electricity generation from wind and photovoltaic (PV) in Germany?

4. **Generation Mix during High Renewable Output**  
   How does Germany’s electricity generation mix change on days with high renewable output (wind and PV), and which conventional sources (lignite, hard coal, gas) decrease the most?

5. **Regional Differences in Electricity Consumption**  
   How does electricity consumption differ between Germany’s TSO control areas (50Hertz, Amprion, TenneT, TransnetBW), and which factors may explain these regional differences?

6. **Correlation between Electricity Consumption and Generation in TSO Regions**  
   To what extent is electricity consumption correlated with electricity generation within Germany’s TSO control areas, and are there observable relationships between regional demand and regional electricity production?

7. **Renewable Generation and Electricity Prices**  
   How are electricity prices related to renewable electricity generation levels, and do high renewable generation periods correspond to lower electricity prices in Germany?

## Topic and Data

The project combines energy market data, weather data, and holiday information to examine Germany-wide and regional electricity patterns. Electricity-related data was obtained from the **SMARD API**, weather data from the **Open-Meteo API**, and holiday or school holiday data was added for calendar-based analysis. [file:434][file:438][file:442]

The regional analysis is based on the four German **TSO control areas** rather than political regions: **50Hertz, Amprion, TenneT, and TransnetBW**. This is important because German electricity data is organized by transmission system structure, not by federal states or cities. [file:441][file:447]

## Data Pipeline

The project follows a structured pipeline from data collection to website output:

1. **Data collection**  
   Data was fetched from APIs and stored locally, mainly in JSON format. [file:434][file:438]

2. **Preprocessing**  
   Timestamps were converted into a consistent datetime format and normalized to a common timezone. Relevant variables, source types, and regions were selected from the raw data. [file:441][file:443][file:448]

3. **Temporal harmonization**  
   Because the original datasets had different time resolutions such as quarter-hourly, hourly, and daily values, all relevant datasets were converted to a **common daily level** before analysis. [file:443][file:444][file:448]

4. **Merging**  
   The processed data was merged by **date** and, where required, by **TSO zone**, resulting in analysis-ready datasets for each research question. [file:443][file:446][file:448]

5. **Analysis and visualization**  
   The project uses correlation analysis, grouped comparisons, scatterplots, line charts, bar charts, and boxplots to answer the research questions and visualize the main findings. [file:442][file:443][file:444][file:445][file:441][file:447][file:448]

## Scripts

The repository contains separate scripts for the main analytical parts of the project:

- `Frage1.py` — public holidays and electricity consumption [file:442]
- `Frage2.py` — seasonal electricity consumption and weather [file:443]
- `Frage3.py` — weather influence on renewable generation [file:444]
- `Frage4.py` — generation mix during high renewable output [file:445]
- `Frage5.py` — regional electricity consumption across TSO zones [file:441]
- `Frage6.py` — correlation between generation and consumption in TSO regions [file:447]
- `Frage7.py` — renewable generation and electricity prices [file:448]

Additional helper or combined scripts may also be included in the repository. [file:434][file:446][file:449]

## Website and Deployment

The website was built as the presentation layer of the project. The analysis was carried out in Python, and the resulting visualizations were embedded into the website together with explanatory text. [file:448]

The website is not connected to live API calls in the browser. Instead, the workflow is: data is fetched in Python, cleaned and transformed, visual outputs are generated, and these outputs are then integrated into the website. [file:434][file:438][file:448]

Replace this section with your actual deployment method, for example:
- GitHub Pages
- university server
- local hosting for presentation purposes

Example placeholders:
- **Live website:** `https://your-project-link`
- **Repository:** `https://your-repository-link`

## Using the Web Application

The website is organized around the research questions and allows users to explore the project results through visualizations and short interpretation texts.

Main highlights include:
- Germany-wide analysis of holiday and seasonal effects
- weather-based renewable generation analysis
- regional comparison across the four TSO zones
- generation-consumption relationships by region
- renewable generation and electricity price analysis

Users can navigate through the sections, read the research focus for each topic, and explore interactive charts where available.

## Code Quality

Because the code is part of the assessment, the project aims to follow good coding practice:
- **PEP 8**
- principles from the **Zen of Python**
- readable naming and structure
- comments for easy comprehensibility

The **README** together with the **code comments** serves as the documentation of the project.

## LLM Marking

According to the project requirements, all code that was directly generated by an LLM or created with substantial LLM assistance must be marked clearly in the source code.

Recommended comment style:

```python
# LLM-assisted: This section was developed with the help of an LLM.
# The code was reviewed, adapted, and tested manually.
