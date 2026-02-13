from datetime import date
from shiny import App, reactive, render, ui
import pandas as pd

# read in the df 
permits_df = pd.read_csv('data/raw/issued-building-permits.csv', sep = ';', encoding = 'utf-8')

permits_df['IssueDate'] = pd.to_datetime(permits_df['IssueDate'])

# find the minimum and maximum issue date dynamically from the data 
EARLIEST_ISSUE_DATE = permits_df['IssueDate'].min().date()
LATEST_ISSUE_DATE = permits_df['IssueDate'].max().date()


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

        #map_placeholder {
          min-height: 360px;
          display: block;
        }

        #trend_placeholder,
        #top_neighbourhoods_placeholder,
        #map_placeholder {
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
        "Vancouver Building Permits: Trends, Processing Times, and Neighbourhood Activity"
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_date_range(
                id="date_range",
                label="Permit issued date range",
                start=EARLIEST_ISSUE_DATE,
                end=LATEST_ISSUE_DATE,
                min=EARLIEST_ISSUE_DATE, # prevent user from selecting dates from outside the earliest and latest permit issuance dates
                max=LATEST_ISSUE_DATE
            ),
            ui.input_checkbox_group(
                id="checkbox_group",
                label="Type of work",
                choices={
                    "Residential": "Residential",
                    "Commercial": "Commercial",
                    "Demolition": "Demolition",
                    "Alteration": "Alteration",
                },
                selected=[
                    "Residential",
                    "Commercial",
                    "Demolition",
                    "Alteration",
                ],
            ),
            ui.input_select(
                id="area",
                label="GeoLocalArea (Neighbourhood)",
                choices=["All", "Placeholder A", "Placeholder B"],
                selected="All",
            ),
            ui.input_action_button("action_button", "Clear Selection"),
            open="desktop",
            width=300,
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Permit Volume Over Time + Forecast"),
                ui.output_text("trend_placeholder"),
                full_screen=True,
            ),
            ui.value_box("Permits Issued (YTD)", ui.output_text("permits_ytd")),
            ui.value_box("Avg Processing Time (YTD)", ui.output_text("avg_days")),
            col_widths=[6, 3, 3],
            fill=False,
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Top Neighbourhoods by Permit Volume (YTD)"),
                ui.output_text("top_neighbourhoods_placeholder"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Building Permit Activity By Neighbourhood"),
                ui.output_text("map_placeholder"),
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
            selected=["Residential", "Commercial", "Demolition", "Alteration"],
        )
        ui.update_select("area", selected="All")

    @render.text
    def permits_ytd():
        return "Placeholder value"

    @render.text
    def avg_days():
        return "Placeholder value"

    @render.text
    def trend_placeholder():
        return (
            "Placeholder: add time-series chart for monthly permit volume by type "
            "(with optional forecast)."
        )

    @render.text
    def top_neighbourhoods_placeholder():
        return (
            "Placeholder: add bar chart of top neighbourhoods by permit volume "
            "for the selected filters."
        )

    @render.text
    def map_placeholder():
        return (
            "Placeholder: add interactive neighbourhood map showing permit activity "
            "intensity."
        )


app = App(app_ui, server)
