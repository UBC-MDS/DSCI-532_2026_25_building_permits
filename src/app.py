from shiny import App, reactive, render, ui


MIN_YEAR = 2019
MAX_YEAR = 2025


app_ui = ui.page_fluid(
    ui.tags.style(
        """
        body { font-size: 0.9em; background-color: #f6f7fb; }
        .placeholder-note { color: #4a4f65; }
        """
    ),
    ui.panel_title(
        "Vancouver Building Permits: Trends, Processing Times, and Neighbourhood Activity"
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_slider(
                id="slider",
                label="Permit issued year range",
                min=MIN_YEAR,
                max=MAX_YEAR,
                value=[MIN_YEAR, MAX_YEAR],
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
            ui.input_action_button("action_button", "Reset filter"),
            open="desktop",
        ),
        ui.layout_columns(
            ui.value_box("Permits Issued (YTD)", ui.output_text("permits_ytd")),
            ui.value_box("Avg Processing Time (YTD)", ui.output_text("avg_days")),
            ui.value_box("Selected Neighbourhood", ui.output_text("selected_area")),
            fill=False,
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Permit Volume Over Time + Forecast"),
                ui.output_text("trend_placeholder"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Top Neighbourhoods by Permit Volume (YTD)"),
                ui.output_text("top_neighbourhoods_placeholder"),
                full_screen=True,
            ),
            col_widths=[6, 6],
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Building Permit Activity By Neighbourhood"),
                ui.output_text("map_placeholder"),
                full_screen=True,
            )
        ),
    ),
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.action_button)
    def _reset_filters():
        ui.update_slider("slider", value=[MIN_YEAR, MAX_YEAR])
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
    def selected_area():
        return input.area()

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
