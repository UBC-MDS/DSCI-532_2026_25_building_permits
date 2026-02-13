# City of Vancouver Building Permits Dashboard

Dashboard built using Python Shiny that explores Building Permit data from the City of Vancouver, starting in 2017. The dashboard allows users to analyze permit volume trends across time and neighbourhood, and show the number of permits issued and average processing time of these permits for this year up until the current date. An interactive map allows for users to click on and interactively filter for specific neighbourhods. Interactive filters such as date range, type of work for the permit, and neighbourhood give city planners and stakeholders a high-level overview of building permit development trends across Vancouver, Canada.

## Get Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
```

```bash
cd DSCI-532_2026_25_building_permits
```

### 2. Create or update the conda environment

```bash
conda env create -f environment.yml || conda env update -f environment.yml
```

```bash
conda activate 532_group_25
```

### 3. Run the dashboard

```bash
shiny run --reload src/app.py
```

Then open the local URL shown in your terminal (usually `http://127.0.0.1:8000`).
