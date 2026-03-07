from datetime import date
import copy
import json
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, render_altair
from faicons import icon_svg
import pandas as pd
import ipyleaflet
from ipywidgets import HTML
import altair as alt

alt.themes.enable("latimes")

# Declare the column names for each filter
ISSUE_DATE = 'IssueDate'
APPLIED_DATE = 'PermitNumberCreatedDate'
AREA = 'GeoLocalArea'
PERMIT_TYPE = 'TypeOfWork'

# Read in the data
permits_df = pd.read_csv('data/raw/issued-building-permits.csv',
                         sep=';',
                         encoding='utf-8')

with open('data/raw/local-area-boundary.geojson', encoding='utf-8') as f:
    neighbourhood_geojson = json.load(f)

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
    ui.tags.link(
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        rel="stylesheet",
    ),
    ui.tags.style(
        """
        :root {
          --accent: #6C5CE7;
          --accent-deep: #5A4BD1;
          --accent-light: rgba(108, 92, 231, 0.07);
          --blue: #0984E3;
          --teal: #00B894;
          --coral: #E17055;
          --surface: #F0F2F8;
          --card-bg: #FFFFFF;
          --card-border: rgba(108, 92, 231, 0.12);
          --text-primary: #2D3436;
          --text-secondary: #636E72;
          --text-muted: #B2BEC3;
          --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
          --shadow-md: 0 4px 14px rgba(108, 92, 231, 0.10);
          --radius: 14px;
        }

        * { box-sizing: border-box; }

        body {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 0.875rem;
          background: var(--surface);
          color: var(--text-primary);
          -webkit-font-smoothing: antialiased;
        }

        .container-fluid {
          max-width: 1440px;
          padding: 0 24px;
        }

        h2 {
          background: linear-gradient(135deg, #6C5CE7, #0984E3);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 800;
          text-align: center;
          margin: 18px 0 10px;
          font-size: 1.7rem;
          letter-spacing: -0.3px;
          line-height: 1.3;
        }

        /* Sidebar */
        .bslib-sidebar-layout > .sidebar {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: var(--radius);
          padding: 20px 16px;
          box-shadow: var(--shadow-sm);
        }

        .sidebar .control-label {
          color: var(--accent);
          font-weight: 600;
          font-size: 0.78rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 8px;
        }

        .shiny-input-checkboxgroup .shiny-options-group { margin-top: 6px; }
        .shiny-input-checkboxgroup .checkbox {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 4px;
        }
        .shiny-input-checkboxgroup .checkbox input[type="checkbox"] {
          margin: 0;
          flex-shrink: 0;
        }
        .shiny-input-checkboxgroup .checkbox label,
        .shiny-input-checkboxgroup label {
          font-size: 0.82rem;
          color: var(--text-secondary);
          margin-bottom: 0;
          line-height: 1.3;
        }

        .form-control, .form-select {
          border: 1.5px solid rgba(108, 92, 231, 0.2);
          border-radius: 10px;
          padding: 8px 12px;
          font-size: 0.82rem;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .form-control:focus, .form-select:focus {
          border-color: var(--accent);
          box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.12);
          outline: none;
        }

        /* Neighbourhood dropdown: show more options at once */
        #area + .selectize-control .selectize-dropdown-content {
          max-height: 360px;
        }
        #area + .selectize-control .option {
          padding-top: 8px;
          padding-bottom: 8px;
        }

        .btn.btn-default, .btn.btn-primary {
          width: 100%;
          background: linear-gradient(135deg, #6C5CE7, #5A4BD1);
          border: none;
          color: #fff;
          font-weight: 600;
          font-size: 0.82rem;
          border-radius: 10px;
          padding: 10px 16px;
          margin-top: 8px;
          transition: transform 0.15s, box-shadow 0.15s;
          cursor: pointer;
        }
        .btn.btn-default:hover, .btn.btn-primary:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 14px rgba(108, 92, 231, 0.35);
        }

        /* Value boxes */
        .bslib-value-box {
          border-radius: var(--radius);
          box-shadow: var(--shadow-sm);
          min-height: 110px;
          transition: box-shadow 0.2s, transform 0.2s;
          border: none;
        }
        .bslib-value-box:hover {
          box-shadow: var(--shadow-md);
          transform: translateY(-2px);
        }
        .bslib-value-box .value-box-title {
          font-size: 0.76rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          opacity: 0.85;
        }
        .bslib-value-box .value-box-value {
          font-size: 1.85rem;
          font-weight: 800;
        }
        .bslib-value-box .value-box-showcase {
          font-size: 2rem;
          opacity: 0.2;
        }
        .vb-purple {
          background: linear-gradient(135deg, #6C5CE7, #a855f7) !important;
          color: #fff !important;
        }
        .vb-purple .value-box-title,
        .vb-purple .value-box-value {
          color: #fff !important;
        }

        /* Cards */
        .card.bslib-card {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: var(--radius);
          box-shadow: var(--shadow-sm);
          overflow: hidden;
          transition: box-shadow 0.2s;
        }
        .card.bslib-card:hover { box-shadow: var(--shadow-md); }
        .card.bslib-card .card-header {
          background: var(--accent-light);
          border-bottom: 1px solid var(--card-border);
          color: var(--accent);
          font-weight: 700;
          font-size: 0.9rem;
          padding: 14px 18px;
        }
        .card.bslib-card .card-body {
          min-height: 240px;
          padding: 16px;
        }

        /* Slider */
        .irs--shiny .irs-bar { background: var(--accent); border-top-color: var(--accent); border-bottom-color: var(--accent); }
        .irs--shiny .irs-handle { border-color: var(--accent); }
        .irs--shiny .irs-from, .irs--shiny .irs-to, .irs--shiny .irs-single { background: var(--accent); }

        /* Map */
        #neighbourhood_map {
          min-height: 420px;
          display: block;
          border-radius: 8px;
          overflow: hidden;
        }

        /* Footer */
        .app-footer {
          text-align: center;
          padding: 16px 0 20px;
          color: var(--text-muted);
          font-size: 0.75rem;
        }
        .app-footer a { color: var(--accent); text-decoration: none; }

        /* Tablet and mobile: value boxes side by side */
        @media (max-width: 992px) {
          .kpi-wrap {
            grid-template-columns: 1fr 1fr !important;
          }
          h2 { font-size: 1.35rem; margin: 14px 0 8px; }
          .bslib-value-box .value-box-value { font-size: 1.4rem; }
          .bslib-value-box { min-height: 100px; }
          .container-fluid { padding: 0 12px; }
          .card.bslib-card .card-body { min-height: 180px; }
          #neighbourhood_map { min-height: 320px; }

          .bslib-sidebar-layout > .main > .bslib-grid {
            grid-template-columns: 1fr !important;
          }
        }

        /* Mobile */
        @media (max-width: 576px) {
          h2 { font-size: 1.15rem; margin: 10px 0 6px; }
          .bslib-value-box .value-box-value { font-size: 1.2rem; }
          .bslib-value-box .value-box-title { font-size: 0.7rem; }
          .bslib-value-box { min-height: 80px; }
          .container-fluid { padding: 0 8px; }
          .card.bslib-card .card-header { font-size: 0.82rem; padding: 10px 14px; }
          .card.bslib-card .card-body { min-height: 160px; padding: 10px; }
          #neighbourhood_map { min-height: 260px; }
          .bslib-sidebar-layout > .sidebar { padding: 14px 12px; }
          .app-footer { font-size: 0.68rem; padding: 12px 0 16px; }
        }
        """
    ),
    ui.panel_title(
        "Vancouver Building Permits"
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div(
                ui.tags.small(
                    "Filter by date, work type, and neighbourhood",
                    style="color: var(--text-muted); display: block; margin-bottom: 16px;",
                ),
            ),
            ui.input_date_range(
                id="date_range",
                label="Date Range",
                start=EARLIEST_ISSUE_DATE,
                end=LATEST_ISSUE_DATE,
                min=EARLIEST_ISSUE_DATE,
                max=LATEST_ISSUE_DATE
            ),
            ui.input_checkbox_group(
                id="checkbox_group",
                label="Type of Work",
                choices=TYPE_CHOICES,
                selected=TYPE_CHOICES,
            ),
            ui.input_selectize(
                id="area",
                label="Neighbourhood",
                choices=AREA_CHOICES,
                selected="All",
                multiple=False,
                options={"placeholder": "Type to search neighbourhood"},
            ),
            ui.tags.script(
                """
                document.addEventListener("shiny:connected", function () {
                  function bindAreaFocusClear() {
                    const el = document.getElementById("area");
                    if (!el || !el.selectize) {
                      setTimeout(bindAreaFocusClear, 200);
                      return;
                    }
                    const sel = el.selectize;
                    const clearSearchOnly = function () {
                      // Clear only the typing text, keep current selected option.
                      if (typeof sel.setTextboxValue === "function") {
                        sel.setTextboxValue("");
                      } else {
                        sel.clearTextbox();
                      }
                    };

                    sel.off("dropdown_open._clearSearch");
                    sel.on("dropdown_open._clearSearch", function () {
                      clearSearchOnly();
                    });

                    if (sel.$control_input) {
                      sel.$control_input.off("focus._clearSearch");
                      sel.$control_input.on("focus._clearSearch", function () {
                        setTimeout(clearSearchOnly, 0);
                      });
                    }
                  }
                  bindAreaFocusClear();
                });
                """
            ),
            ui.input_action_button("action_button", "Reset Filters"),
            open="desktop",
            width=280,
        ),
        ui.layout_column_wrap(
            ui.value_box(
                "Permits Issued",
                ui.output_text("permits_to_date"),
                showcase=icon_svg("file-lines", width="40px"),
                theme="primary",
            ),
            ui.value_box(
                "Avg Processing Time",
                ui.output_text("avg_days"),
                showcase=icon_svg("clock", width="40px"),
                class_="vb-purple",
            ),
            width=1/2,
            class_="kpi-wrap",
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Permit Volume Over Time"),
                output_widget("permit_volume_trend"),
                full_screen=True,
            ),
            col_widths=[12],
            fill=False,
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Neighbourhood Permit Map"),
                output_widget("neighbourhood_map"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Top Neighbourhoods"),
                ui.input_slider("top_n", "Number of Neighbourhoods", min=5, max=20, value=5),
                output_widget("top_neighborhoods"),
                full_screen=True,
            ),
            col_widths={"sm": [12, 12], "lg": [7, 5]},
        ),
        ui.tags.div(
            "Vancouver Building Permits Dashboard | ",
            ui.tags.a("GitHub", href="https://github.com/UBC-MDS/DSCI-532_2026_25_building_permits", target="_blank"),
            " | Data: City of Vancouver Open Data Portal",
            class_="app-footer",
        ),
    ),
)


def server(input, output, session):
    selected_area = reactive.Value("All")

    @reactive.effect
    def _sync_selected_area():
        area = input.area()
        if area in AREA_CHOICES:
            selected_area.set(area)

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
        selected_area.set("All")
        ui.update_selectize("area", selected="All")
        ui.update_slider("top_n", value=5)

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

        # If the user clears all work types manually, show no matching rows.
        if len(types) == 0:
            return df.iloc[0:0]

        df = df[df[PERMIT_TYPE].isin(types)]

        # Filter based on selected neighbourhood from searchable dropdown.
        area = selected_area.get()
        if area != "All":
            df = df[df[AREA] == area]

        return df

    @render.text
    def permits_to_date():
        # Count of permits based on selected filters/filtered_df
        return f"{len(filtered_df()):,}"

    @render.text
    def avg_days():
        df = filtered_df()
        if df.empty:
            return "0 Days"
        
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
                x=alt.X('month:T', scale=alt.Scale(domain=[str(start), str(end)]), title='Year',
                        axis=alt.Axis(titleFontWeight='bold')),
                y=alt.Y('count:Q', title='Count',
                        axis=alt.Axis(titleFontWeight='bold')),
            )
            .properties(background="transparent")
            .configure_view(strokeWidth=0, fill="transparent")
            .mark_line(color="#6C5CE7", strokeWidth=2.5)
        )

        return chart

    @render_widget
    def top_neighborhoods():
        df = filtered_df().copy()
        n = input.top_n()

        top = (
            df.groupby('GeoLocalArea')
            .size()
            .reset_index(name='count')
            .nlargest(n, 'count')
            .sort_values('count', ascending=False)
        )

        chart = (
            alt.Chart(top)
            .mark_bar()
            .encode(
                x=alt.X('count:Q', title='Permit Count'),
                y=alt.Y('GeoLocalArea:N', sort='-x', title='Neighborhood',
                        axis=alt.Axis(titleFontWeight='bold')),
                tooltip=['GeoLocalArea', 'count']
            )
            .properties(background="transparent")
            .configure_view(strokeWidth=0, fill="transparent")
            .configure_mark(color="#6C5CE7")
        )
        return chart

    @reactive.calc
    def map_df():
        df = filtered_df()

        # if empty, return an empty df with expected columns
        if df.empty:
            return pd.DataFrame(columns=[AREA, "permit_count"])

        grouped = (
            df.groupby(AREA)
            .size()
            .reset_index(name="permit_count")
        )

        return grouped

    @render_widget
    def neighbourhood_map():
        df = map_df()
        active_area = selected_area.get()

        center = (49.26, -123.12)
        m = ipyleaflet.Map(
            center=center,
            zoom=12,
            layout={'height': '420px'},
            basemap=ipyleaflet.basemaps.CartoDB.Positron,
            zoom_delta=0.5,
            zoom_snap=0.5,
            scroll_wheel_zoom=False,
            touch_zoom=True,
            double_click_zoom=False,
        )

        counts = dict(zip(df[AREA], df["permit_count"])) if not df.empty else {}

        geojson_data = copy.deepcopy(neighbourhood_geojson)
        for feature in geojson_data["features"]:
            area_name = feature["properties"]["name"]
            count = int(counts.get(area_name, 0))
            feature["properties"]["permit_count"] = count

        def geometry_bounds(geometry):
            min_lat, min_lon = 90.0, 180.0
            max_lat, max_lon = -90.0, -180.0

            def walk(coords):
                nonlocal min_lat, min_lon, max_lat, max_lon
                if not coords:
                    return
                if isinstance(coords[0], (int, float)) and len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                    return
                for item in coords:
                    walk(item)

            walk(geometry.get("coordinates", []))
            return min_lat, min_lon, max_lat, max_lon

        geo_layer = ipyleaflet.GeoJSON(
            data=geojson_data,
            style={
                "color": "#4B5563",
                "weight": 1.2,
                "dashArray": "6 4",
                "fillColor": "#E5E7EB",
                "fillOpacity": 0.35,
            },
            hover_style={
                "color": "#1D4ED8",
                "weight": 2.0,
                "dashArray": "6 4",
                "fillColor": "#3B82F6",
                "fillOpacity": 0.65,
            },
        )
        m.add(geo_layer)

        selected_layer = None
        # Strong, persistent border highlight for selected neighbourhood.
        if active_area != "All":
            selected_feature = next(
                (
                    feature for feature in geojson_data["features"]
                    if feature["properties"]["name"] == active_area
                ),
                None,
            )
            if selected_feature is not None:
                selected_layer = ipyleaflet.GeoJSON(
                    data={"type": "FeatureCollection", "features": [selected_feature]},
                    style={
                        "color": "#1D4ED8",
                        "weight": 4,
                        "dashArray": "2 0",
                        "fillColor": "#DBEAFE",
                        "fillOpacity": 0.0,
                    },
                    hover_style={
                        "color": "#1D4ED8",
                        "weight": 4,
                        "dashArray": "2 0",
                        "fillColor": "#3B82F6",
                        "fillOpacity": 0.65,
                    },
                )
                m.add(selected_layer)

        # Neighbourhood features currently visible after filtering.
        selected_areas = set(df[AREA].tolist()) if not df.empty else set()
        relevant_features = [
            f for f in geojson_data["features"]
            if not selected_areas or f["properties"]["name"] in selected_areas
        ]

        hover_info = HTML(value="")
        hover_control = ipyleaflet.WidgetControl(widget=hover_info, position="topright")

        def hide_hover_info():
            hover_info.value = ""
            if hover_control in m.controls:
                m.remove(hover_control)

        def update_hover_info(**kwargs):
            props = kwargs.get("properties") or {}
            name = props.get("name")
            count = props.get("permit_count", 0)

            if not name:
                hide_hover_info()
                return

            hover_info.value = f"<b>{name}</b><br>Permits: {count:,}"
            if hover_control not in m.controls:
                m.add(hover_control)

        def clear_on_mouseout(**kwargs):
            if kwargs.get("type") in ("mouseout", "mouseleave"):
                hide_hover_info()

        if hasattr(geo_layer, "on_hover"):
            geo_layer.on_hover(update_hover_info)
        if selected_layer is not None and hasattr(selected_layer, "on_hover"):
            selected_layer.on_hover(update_hover_info)
        if hasattr(m, "on_interaction"):
            m.on_interaction(clear_on_mouseout)

        # Auto-zoom so all filtered/selected neighbourhoods are visible.
        if relevant_features:
            south, west = 90.0, 180.0
            north, east = -90.0, -180.0
            for feature in relevant_features:
                min_lat, min_lon, max_lat, max_lon = geometry_bounds(feature["geometry"])
                south = min(south, min_lat)
                west = min(west, min_lon)
                north = max(north, max_lat)
                east = max(east, max_lon)
            if active_area == "All":
                lat_pad = max(0.002, (north - south) * 0.05)
                lon_pad = max(0.002, (east - west) * 0.05)
            else:
                # Keep a wider local context when a single neighbourhood is selected.
                lat_pad = max(0.02, (north - south) * 0.50)
                lon_pad = max(0.02, (east - west) * 0.50)
            m.fit_bounds([
                (south - lat_pad, west - lon_pad),
                (north + lat_pad, east + lon_pad),
            ])

        return m


app = App(app_ui, server)
