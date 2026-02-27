from datetime import date
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, render_altair
import pandas as pd
import ipyleaflet
from ipywidgets import HTML
import altair as alt

# Declare the column names for each filter
ISSUE_DATE = 'IssueDate'
APPLIED_DATE = 'PermitNumberCreatedDate'
AREA = 'GeoLocalArea'
PERMIT_TYPE = 'TypeOfWork'

# Read in the data
permits_df = pd.read_csv('data/raw/issued-building-permits.csv',
                         sep=';',
                         encoding='utf-8')

# Standarsize dates and strip whitespace for values we want to filter on
permits_df[ISSUE_DATE] = pd.to_datetime(permits_df[ISSUE_DATE])
permits_df[PERMIT_TYPE] = permits_df[PERMIT_TYPE].astype(str).str.strip()

# Find the minimum and maximum issue date dynamically from the data
EARLIEST_ISSUE_DATE = permits_df[ISSUE_DATE].min().date()
LATEST_ISSUE_DATE = permits_df[ISSUE_DATE].max().date()

# Find the unique areas/neighbourhoods from the data
areas = sorted(
    permits_df[AREA]
    .dropna()
    .astype(str)
    .unique()
)

AREA_CHOICES = ['All'] + areas

# Find the unique permit types to pass in to the sidebar filter below
TYPE_CHOICES = sorted(
    permits_df[PERMIT_TYPE]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

app_ui = ui.page_fluid(
    ui.tags.style(
        """
        :root {
          --brand: #2d2aa8;
          --brand-soft: #4d4a95;
          --surface: #f6f7fb;
          --card-bg: #ffffff;
          --card-border: #dfe2ef;
          --muted: #4a4f65;
        }

        body {
          font-size: 0.9em;
          background-color: var(--surface);
          color: #1d2333;
        }

        .container-fluid {
          max-width: 1500px;
          padding-left: 18px;
          padding-right: 18px;
        }

        h2 {
          color: var(--brand);
          font-weight: 800;
          text-align: center;
          margin-top: 16px;
          margin-bottom: 16px;
          font-size: 2.4rem;
          line-height: 1.2;
        }

        .bslib-sidebar-layout > .sidebar {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 10px;
          padding: 14px 14px 18px 14px;
        }

        .sidebar .control-label {
          color: var(--brand);
          font-weight: 700;
          margin-bottom: 6px;
        }

        .shiny-input-checkboxgroup .shiny-options-group {
          margin-top: 10px;
        }

        .form-control,
        .form-select {
          border: 1px solid #cfd5ea;
          border-radius: 8px;
        }

        .btn.btn-default,
        .btn.btn-primary {
          width: 100%;
          background: var(--brand);
          border-color: var(--brand);
          color: #fff;
          font-weight: 600;
          border-radius: 8px;
        }

        .bslib-value-box {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 10px;
          min-height: 138px;
        }

        .bslib-value-box .value-box-title {
          color: var(--brand-soft);
          font-size: 0.98rem;
          font-weight: 700;
        }

        .bslib-value-box .value-box-value {
          font-size: 1.55rem;
          font-weight: 800;
          color: #111827;
        }

        .card.bslib-card {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 10px;
          box-shadow: none;
        }

        .card.bslib-card .card-header {
          background: transparent;
          border-bottom: 1px solid #edf0fb;
          color: var(--brand-soft);
          font-weight: 700;
          font-size: 1.25rem;
        }

        .card.bslib-card .card-body {
          min-height: 220px;
        }

        #neighbourhood_map {
          min-height: 400px;
          display: block;
        }

        #permit_volume_trend,
        #top_neighbourhoods {
          border: 1px dashed #a7b0d2;
          border-radius: 8px;
          padding: 14px;
          background: #f1f3fa;
          color: var(--muted);
          line-height: 1.45;
        }
        """
    ),
    ui.panel_title(
        "Vancouver Building Permits: Trends, Processing Times,"
        "and Neighbourhood Activity"
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_date_range(
                id="date_range",
                label="Permit issued date range",
                start=EARLIEST_ISSUE_DATE,
                end=LATEST_ISSUE_DATE,
                min=EARLIEST_ISSUE_DATE,
                max=LATEST_ISSUE_DATE
            ),
            ui.input_checkbox_group(
                id="checkbox_group",
                label="Type of work",
                choices=TYPE_CHOICES,
                selected=TYPE_CHOICES,
            ),
            ui.input_select(
                id="area",
                label="GeoLocalArea (Neighbourhood)",
                choices=AREA_CHOICES,
                selected="All",
            ),
            ui.input_action_button("action_button", "Clear Selection"),
            open="desktop",
            width=300,
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Permit Volume Over Time"),
                output_widget("permit_volume_trend"),
                full_screen=True,
            ),
            ui.value_box("Permits Issued", ui.output_text("permits_to_date")),
            ui.value_box("Avg Processing Time", ui.output_text("avg_days")),
            col_widths=[6, 3, 3],
            fill=False,
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Top Neighbourhoods by Permit Volume"),
                ui.output_text("top_neighbourhoods"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Building Permit Activity By Neighbourhood"),
                output_widget("neighbourhood_map"),
                full_screen=True,
            ),
            col_widths=[6, 6],
        ),
    ),
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.action_button)
    def _reset_filters():
        ui.update_date_range(
            "date_range",
            start=EARLIEST_ISSUE_DATE,
            end=LATEST_ISSUE_DATE,
        )
        ui.update_checkbox_group(
            "checkbox_group",
            selected=TYPE_CHOICES,
        )
        ui.update_select("area", selected="All")

    @reactive.calc
    def filtered_df():
        df = permits_df.copy()

        # Filter based on the inputted date
        start, end = input.date_range()
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        # Filter for rows between the start and end date (mutually inclusive)
        df = df[(df[ISSUE_DATE] >= start) & (df[ISSUE_DATE] <= end)]

        # Filter the df so it only contains the permit types checked off
        types = list(input.checkbox_group())
        if types:
            df = df[df[PERMIT_TYPE].isin(types)]

        # Filter based on the area/neighbourhood selected (drop down so only
        # one area/neighbourhood can be selected)
        area = input.area()
        if area != "All":
            # Filter df to only contain selected area
            df = df[df[AREA] == area]

        return df

    @render.text
    def permits_to_date():
        # Count of permits based on selected filters/filtered_df
        return f"{len(filtered_df()):,}"

    @render.text
    def avg_days():
        df = filtered_df()

        applied_date = pd.to_datetime(df[APPLIED_DATE], errors="coerce")
        issue_date = pd.to_datetime(df[ISSUE_DATE], errors="coerce")

        days_taken_to_issue = (issue_date - applied_date).dt.days
        days_taken_to_issue = days_taken_to_issue.dropna()

        return f"{days_taken_to_issue.mean():.1f} Days"

    @render_altair
    def permit_volume_trend():
        df = filtered_df().copy()
        df[ISSUE_DATE] = pd.to_datetime(df[ISSUE_DATE])
        df['month'] = df[ISSUE_DATE].dt.to_period('M').dt.to_timestamp()

        monthly = (
            df.groupby('month')
            .size()
            .reset_index(name='count')
        )

        start, end = input.date_range()

        chart = (
            alt.Chart(monthly)
            .mark_line()
            .encode(
                x=alt.X('month:T', scale=alt.Scale(domain=[str(start), str(end)]), title='Year'),
                y=alt.Y('count:Q', title='Count'),
            )
        )

        return chart

    @render.text
    def top_neighbourhoods():
        return (
            "Placeholder: add bar chart of top neighbourhoods by permit volume"
            "for the selected filters."
        )

    @reactive.calc
    def map_df():
        df = filtered_df()
        df = df.dropna(subset=['geo_point_2d'])

        coords = df['geo_point_2d'].astype(str).str.split(',', expand=True)
        df = df.copy()
        df['lat'] = pd.to_numeric(coords[0].str.strip(), errors='coerce')
        df['lon'] = pd.to_numeric(coords[1].str.strip(), errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])

        grouped = df.groupby(AREA).agg(
            permit_count=('lat', 'size'),
            lat=('lat', 'mean'),
            lon=('lon', 'mean')
        ).reset_index()

        return grouped

    @render_widget
    def neighbourhood_map():
        df = map_df()

        center = (49.26, -123.12)
        m = ipyleaflet.Map(center=center, zoom=12, layout={'height': '400px'})

        if df.empty:
            return m

        max_count = df['permit_count'].max()

        for _, row in df.iterrows():
            radius = max(5, int((row['permit_count'] / max_count) * 40))
            marker = ipyleaflet.CircleMarker(
                location=(row['lat'], row['lon']),
                radius=radius,
                color='#2d2aa8',
                fill_color='#4d4a95',
                fill_opacity=0.6,
                weight=2,
            )
            popup_content = HTML(value=f"<b>{row[AREA]}</b><br>Permits:{row['permit_count']:,}")
            marker.popup = popup_content
            m.add(marker)

        return m


app = App(app_ui, server)
