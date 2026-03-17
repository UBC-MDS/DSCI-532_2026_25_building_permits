from datetime import date
import json
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, render_altair, reactive_read
from faicons import icon_svg
import pandas as pd
import altair as alt
import chatlas as clt
import os
from matplotlib.colors import LinearSegmentedColormap, to_hex
from querychat import QueryChat
from dotenv import load_dotenv
import ibis 
from ibis import _ # _ is a shortcut for referencing columns in an ibis table expression without typing table name. ex) permits.filter(_.project_value < 10000) compared to permits.filter(permits.project_value < 10000)

from utils import get_unique_sorted, compute_avg_days

load_dotenv()

alt.themes.enable("latimes")

# Declare the column names for each filter
ISSUE_DATE = 'IssueDate'
APPLIED_DATE = 'PermitNumberCreatedDate'
AREA = 'GeoLocalArea'
PERMIT_TYPE = 'TypeOfWork'

permits_df = pd.read_parquet("data/processed/issued-building-permits.parquet")

with open('data/raw/local-area-boundary.geojson', encoding='utf-8') as f:
    neighbourhood_geojson = json.load(f)

# Standarsize dates and strip whitespace for values we want to filter on
permits_df[ISSUE_DATE] = pd.to_datetime(permits_df[ISSUE_DATE])
permits_df[PERMIT_TYPE] = permits_df[PERMIT_TYPE].astype(str).str.strip()

# create the GitHub chat client using the GITHUB_TOKEN in .env
chat_client = clt.ChatGithub(
    api_key=os.environ["GITHUB_TOKEN"],
    model="gpt-4.1-mini"
)

query_chat = QueryChat(permits_df, "building_permits", client=chat_client)

# Find the minimum and maximum issue date dynamically from the data
EARLIEST_ISSUE_DATE = permits_df[ISSUE_DATE].min().date()
LATEST_ISSUE_DATE = permits_df[ISSUE_DATE].max().date()

# Find the unique areas/neighbourhoods from the data
areas = get_unique_sorted(permits_df[AREA])

AREA_CHOICES = ['All'] + areas

# Find the unique permit types to pass in to the sidebar filter below
TYPE_CHOICES = get_unique_sorted(permits_df[PERMIT_TYPE])

MAP_HEAT_COLORS = ["#F5F3FF", "#DDD6FE", "#A78BFA", "#7C3AED", "#5B21B6"]
MAP_HEAT_CMAP = LinearSegmentedColormap.from_list("permit_heat", MAP_HEAT_COLORS)


def heat_fill_color(count, max_count):
    if max_count <= 0:
        return "#E5E7EB"
    scale_value = min(max(count / max_count, 0.0), 1.0)
    return to_hex(MAP_HEAT_CMAP(scale_value))


def legend_ticks(max_count):
    if max_count <= 0:
        return [0] * 10
    return [round(max_count * step / 9) for step in range(10)]


def format_legend_tick(value):
    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1000:
        compact = value / 1000
        if float(compact).is_integer():
            return f"{int(compact)}k"
        return f"{compact:.1f}k"

    if value.is_integer():
        return f"{int(value)}"
    return f"{value:.1f}"


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


def padded_bounds(features, lat_pad_ratio=0.10, lon_pad_ratio=0.10, min_pad=0.01):
    south, west = 90.0, 180.0
    north, east = -90.0, -180.0

    for feature in features:
        min_lat, min_lon, max_lat, max_lon = geometry_bounds(feature["geometry"])
        south = min(south, min_lat)
        west = min(west, min_lon)
        north = max(north, max_lat)
        east = max(east, max_lon)

    lat_pad = max(min_pad, (north - south) * lat_pad_ratio)
    lon_pad = max(min_pad, (east - west) * lon_pad_ratio)

    return [
        (south - lat_pad, west - lon_pad),
        (north + lat_pad, east + lon_pad),
    ]


INITIAL_MAP_BOUNDS = padded_bounds(
    neighbourhood_geojson["features"],
    lat_pad_ratio=0.12,
    lon_pad_ratio=0.12,
    min_pad=0.012,
)


app_ui = ui.page_fluid(
    ui.busy_indicators.use(spinners=False),
    ui.tags.link(
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        rel="stylesheet",
    ),
    ui.tags.link(
        rel="stylesheet",
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    ),
    ui.tags.script(src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"),
    ui.tags.script("""
(function() {
    var _map = null, _geoLayer = null, _legend = null;

    Shiny.addCustomMessageHandler('update_nbhd_map', function(msg) {
        var container = document.getElementById('leaflet-nbhd-map');
        if (!container) return;

        if (!_map) {
            _map = L.map(container, {
                zoomControl: false,
                scrollWheelZoom: false,
                doubleClickZoom: false,
                zoomDelta: 0.5,
                zoomSnap: 0.5,
            });
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19,
            }).addTo(_map);
            L.control.zoom({ position: 'bottomleft' }).addTo(_map);
            _map.fitBounds(msg.bounds);
        }

        if (_geoLayer) _map.removeLayer(_geoLayer);
        _geoLayer = L.geoJSON(msg.data, {
            style: function(feature) {
                if (feature.properties.isSelected) {
                    return { color: '#7C3AED', weight: 4, dashArray: '10 4',
                             fillColor: feature.properties.fillColor,
                             fillOpacity: feature.properties.fillOpacity };
                }
                return { color: '#4B5563', weight: 1.2, dashArray: '6 4',
                         fillColor: feature.properties.fillColor,
                         fillOpacity: feature.properties.fillOpacity };
            },
            onEachFeature: function(feature, layer) {
                layer.on('click', function() {
                    Shiny.setInputValue('map_click', feature.properties.name, { priority: 'event' });
                });
                layer.on('mouseover', function(e) {
                    e.target.setStyle({ color: '#2563EB', weight: 2.2, dashArray: '6 4', fillOpacity: 0.82 });
                    e.target.bringToFront();
                });
                layer.on('mouseout', function(e) { _geoLayer.resetStyle(e.target); });
                layer.bindTooltip(
                    '<strong>' + feature.properties.name + '</strong><br>Permits: ' + feature.properties.permit_count,
                    { sticky: true }
                );
            },
        }).addTo(_map);

        if (_legend) _map.removeControl(_legend);
        _legend = L.control({ position: 'bottomright' });
        _legend.onAdd = function() {
            var div = L.DomUtil.create('div');
            div.style.cssText = 'background:#fff;border-radius:8px;padding:8px 10px;box-shadow:0 1px 5px rgba(0,0,0,0.15);font-family:Inter,sans-serif;font-size:0.72rem;color:#2D3436;min-width:54px;';
            var lbl = msg.tick_labels;
            div.innerHTML =
                '<div style="font-weight:700;font-size:0.73rem;color:#6C5CE7;margin-bottom:6px;text-align:center;">Permit Count</div>' +
                '<div style="display:flex;align-items:stretch;gap:6px;">' +
                    '<div style="width:14px;height:160px;border-radius:3px;background:linear-gradient(to bottom,#5B21B6,#7C3AED,#A78BFA,#DDD6FE,#F5F3FF);flex-shrink:0;"></div>' +
                    '<div style="display:flex;flex-direction:column;justify-content:space-between;height:160px;line-height:1;">' +
                        '<span>' + lbl[0] + '</span><span>' + lbl[1] + '</span><span>' + lbl[2] + '</span>' +
                        '<span>' + lbl[3] + '</span><span>' + lbl[4] + '</span>' +
                    '</div>' +
                '</div>';
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        _legend.addTo(_map);
    });
})();
"""),
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

        @keyframes selected-neighbourhood-dash {
          to { stroke-dashoffset: -28; }
        }

        .selected-neighbourhood-path {
          animation: selected-neighbourhood-dash 1.2s linear infinite;
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

        /* Value boxes – compact */
        .bslib-value-box {
          border-radius: var(--radius);
          box-shadow: var(--shadow-sm);
          min-height: auto !important;
          overflow: hidden !important;
          transition: box-shadow 0.2s, transform 0.2s;
          border: none;
          overflow: hidden;
        }
        .bslib-value-box .card-body {
          padding: 6px 12px !important;
        }
        .bslib-value-box .value-box-grid {
          --bslib-grid-height: auto !important;
          --bslib-grid-height-mobile: auto !important;
          min-height: 0 !important;
          display: block !important;
          position: relative;
        }
        .bslib-value-box:hover {
          box-shadow: var(--shadow-md);
          transform: translateY(-2px);
        }
        .bslib-value-box .value-box-title {
          font-size: 0.62rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          opacity: 0.85;
          margin-bottom: 0;
        }
        .bslib-value-box .value-box-value {
          font-size: 1.15rem;
          font-weight: 800;
          line-height: 1.1;
          min-height: 1.27rem;
        }
        .bslib-value-box .value-box-showcase {
          opacity: 0.25;
          padding: 4px !important;
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          z-index: 0;
          width: auto !important;
          max-width: none !important;
        }
        .bslib-value-box .value-box-area {
          padding: 6px 8px !important;
          min-height: 0 !important;
          display: flex !important;
          flex-direction: column !important;
          justify-content: center !important;
          text-align: center !important;
          width: 100% !important;
          position: relative;
          z-index: 1;
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
        .card.bslib-card.bslib-value-box .card-body {
          min-height: auto !important;
          padding: 6px 12px !important;
        }

        /* Slider */
        .irs--shiny .irs-bar { background: var(--accent); border-top-color: var(--accent); border-bottom-color: var(--accent); }
        .irs--shiny .irs-handle { border-color: var(--accent); }
        .irs--shiny .irs-from, .irs--shiny .irs-to, .irs--shiny .irs-single { background: var(--accent); }

        /* Map */
        .leaflet-interactive:focus { outline: none; }
        #leaflet-nbhd-map { border-radius: 8px; overflow: hidden; }

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
          .bslib-value-box .value-box-value { font-size: 1.15rem; }
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
          .bslib-value-box .value-box-value { font-size: 0.95rem; }
          .bslib-value-box .value-box-title { font-size: 0.6rem; }
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
    ui.navset_tab(
        ui.nav_panel(
            "Dashboard",
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
                ui.panel_conditional(
                    "input.checkbox_group !== null && input.checkbox_group.length === 0",
                    ui.tags.div(
                        ui.tags.div(
                            ui.tags.span("No filters selected", style="font-weight:700; font-size:1.1rem;"),
                            ui.tags.br(),
                            ui.tags.span(
                                "Select at least one work type from the sidebar to view results.",
                                style="opacity:0.7; font-size:0.9rem;",
                            ),
                            style="text-align:center; padding:32px 16px; color:var(--accent);",
                        ),
                        style="background:var(--accent-light); border:1px dashed var(--accent); border-radius:var(--radius); margin-bottom:12px;",
                    ),
                ),
                ui.layout_column_wrap(
            ui.value_box(
                "Permits Issued",
                ui.output_text("permits_to_date"),
                showcase=icon_svg("file-lines", width="22px"),
                theme="primary",
                showcase_layout="left center",
            ),
            ui.value_box(
                "Avg Processing Time",
                ui.output_text("avg_days"),
                showcase=icon_svg("clock", width="22px"),
                class_="vb-purple",
                showcase_layout="left center",
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
                ui.tags.div(id="leaflet-nbhd-map", style="height:420px;"),
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
        ),
        ui.nav_panel(
            "AI",
            ui.layout_columns(
                ui.card(
                    ui.card_header("AI Data Helper Chat"),
                    query_chat.ui(),
                    full_screen=False,
                    height="70vh",
                ),
                ui.card(
                    ui.card_header("Filtered DataFrame"),
                    ui.output_data_frame("ai_df_preview"),
                    ui.download_button(
                        "download_ai_df",
                        "Download CSV"
                    ),
                    full_screen=False,
                    height="70vh",
                ),
                col_widths={"lg": [6, 6], "sm": [12, 12]},
                fill=True,
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Permit Volume Over Time"),
                    output_widget("ai_permit_volume_trend"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Top Neighbourhoods"),
                    output_widget("ai_top_neighborhoods"),
                    full_screen=True,
                ),
                col_widths={"lg": [6, 6], "sm": [12, 12]},
            ),
        ),
    ),
)

def server(input, output, session):
    # connect to the data from the parquet file using ibis/DuckDB
    conn = ibis.duckdb.connect()
    permits = conn.read_parquet("data/processed/issued-building-permits.parquet")
    session.on_ended(conn.disconnect)
    selected_area = reactive.Value("All")
    qc_vals = query_chat.server()

    def get_time_axis(start, end):
        '''
        Formats the time axis as yearly if there is a wide date range (over 2 years)
        Otherwise formats the time axis as month/yaer if the date range is shorter.
        '''
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        days = (end - start).days

        # if there is a wide date range, show years on axis
        if days > 730:
            return alt.Axis(
                title = "Year",
                format = "%Y",
                tickCount = "year",
                titleFontWeight = "bold",
                labelAngle = 0
            )
        
        # else return shorter date range 
        return alt.Axis(
            title="Month",
            format="%b %Y",
            tickCount=8,
            titleFontWeight="bold",
            labelAngle=0
        )

    @reactive.effect
    def _sync_selected_area():
        area = input.area()
        if area in AREA_CHOICES:
            selected_area.set(area)

    def apply_area_selection(area_name: str) -> None:
        if area_name in AREA_CHOICES:
            selected_area.set(area_name)
            ui.update_selectize("area", selected=area_name)

    @reactive.calc
    def ai_df():
        return qc_vals.df()

    @render.download(filename=lambda: f"ai_filtered_permits_{date.today()}.csv")
    def download_ai_df():
        yield ai_df().to_csv(index=False)

    @render.data_frame
    def ai_df_preview():
        return ai_df()

    @render_widget
    def ai_permit_volume_trend():
        df = ai_df().copy()

        if ISSUE_DATE not in df.columns or df.empty:
            return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_point()

        df[ISSUE_DATE] = pd.to_datetime(df[ISSUE_DATE])
        df['month'] = df[ISSUE_DATE].dt.to_period('M').dt.to_timestamp()

        monthly = (
            df.groupby('month')
            .size()
            .reset_index(name='count')
            .sort_values('month')
        )

        start = monthly["month"].min()
        end = monthly["month"].max()

        axis_config = get_time_axis(start, end)

        base = alt.Chart(monthly).encode(
            x=alt.X(
                'month:T',
                axis=axis_config
            ),
            y=alt.Y(
                'count:Q', 
                title='Count',
                axis=alt.Axis(titleFontWeight='bold')
            ),
        )

        line = base.mark_line(color="#6C5CE7", strokeWidth=2.5)

        points = base.mark_point(color="#6C5CE7", size=30, opacity=0).encode(
            tooltip=[
                alt.Tooltip('month:T', title='Month', format='%b %Y'),
                alt.Tooltip('count:Q', title='Permits'),
            ]
        )

        chart = (
            (line + points)
            .properties(background="transparent")
            .configure_view(strokeWidth=0, fill="transparent")
        )
        return chart

    @render_widget
    def ai_top_neighborhoods():
        df = ai_df().copy()

        if AREA not in df.columns or df.empty:
            return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_point()

        top = (
            df.groupby(AREA)
            .size()
            .reset_index(name='count')
            .nlargest(10, 'count')
            .sort_values('count', ascending=False)
        )

        chart = (
            alt.Chart(top)
            .mark_bar()
            .encode(
                x=alt.X('count:Q', title='Permit Count'),
                y=alt.Y(f'{AREA}:N', sort='-x', title='Neighbourhood',
                        axis=alt.Axis(titleFontWeight='bold')),
                tooltip=[AREA, 'count'],
            )
            .properties(background="transparent")
            .configure_view(strokeWidth=0, fill="transparent")
            .configure_mark(color="#6C5CE7")
        )
        return chart

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
    def filtered_expr():
        # Filter based on the inputted date
        start, end = input.date_range()
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        expr = permits

        # Filter for rows between the start and end date (mutually inclusive)
        expr = expr.filter(
            _[ISSUE_DATE].between(start, end)
        )

        # Filter the df so it only contains the permit types checked off
        types = list(input.checkbox_group())

        # If the user clears all work types manually, show no matching rows.
        if len(types) == 0:
            expr = expr.filter(
                _[PERMIT_TYPE].isin([])
            )
            return expr

        expr = expr.filter(_[PERMIT_TYPE].isin(types))

        # Filter based on selected neighbourhood from searchable dropdown.
        area = selected_area.get()
        if area != "All":
            expr = expr.filter(_[AREA] == area)

        return expr
    
    @reactive.calc
    def filtered_df():
        return filtered_expr().execute()

    @render.text
    def permits_to_date():
        # Count of permits based on selected filters/filtered_df
        return f"{filtered_expr().count().execute():,}"

    @render.text
    def avg_days():
        return compute_avg_days(filtered_df(), APPLIED_DATE, ISSUE_DATE)

    @render_altair
    def permit_volume_trend():
        df = filtered_df().copy()
        df[ISSUE_DATE] = pd.to_datetime(df[ISSUE_DATE])
        df['month'] = df[ISSUE_DATE].dt.to_period('M').dt.to_timestamp()

        monthly = (
            df.groupby('month')
            .size()
            .reset_index(name='count')
            .sort_values('month')
        )

        start, end = input.date_range()
        axis_config = get_time_axis(start, end)

        base = alt.Chart(monthly).encode(
            x=alt.X(
                'month:T', 
                scale=alt.Scale(domain=[pd.to_datetime(start), pd.to_datetime(end)]),
                axis=axis_config
            ),
            y=alt.Y(
                'count:Q', 
                title='Count',
                axis=alt.Axis(titleFontWeight='bold')
            ),
        )

        line = base.mark_line(color="#6C5CE7", strokeWidth=2.5)

        points = base.mark_point(color="#6C5CE7", size=30, opacity=0).encode(
            tooltip=[
                alt.Tooltip('month:T', title='Month', format='%b %Y'),
                alt.Tooltip('count:Q', title='Permits'),
            ]
        )

        chart = (
            (line + points)
            .properties(background="transparent")
            .configure_view(strokeWidth=0, fill="transparent")
        )

        return chart

    @render_altair
    def top_neighborhoods():
        df = filtered_df().copy()
        n = input.top_n()
        active_area = selected_area.get()

        top = (
            df.groupby(AREA)
            .size()
            .reset_index(name='count')
            .nlargest(n, 'count')
            .sort_values('count', ascending=False)
        )

        top["is_selected"] = top[AREA].eq(active_area)

        selected_bar = alt.selection_point(
            name="selected_bar",
            fields=[AREA],
            on="click",
            clear=False,
            empty=True,
            toggle=False,
        )

        chart = (
            alt.Chart(top)
            .mark_bar()
            .encode(
                x=alt.X('count:Q', title='Permit Count'),
                y=alt.Y(f'{AREA}:N', sort='-x', title='Neighborhood',
                        axis=alt.Axis(titleFontWeight='bold')),
                color=alt.condition(
                    alt.datum.is_selected,
                    alt.value("#6C5CE7"),
                    alt.value("#C8BFF7"),
                ),
                stroke=alt.condition(
                    alt.datum.is_selected,
                    alt.value("#5A4BD1"),
                    alt.value("#C8BFF7"),
                ),
                strokeWidth=alt.condition(
                    alt.datum.is_selected,
                    alt.value(1.2),
                    alt.value(0),
                ),
                tooltip=[AREA, 'count']
            )
            .add_params(selected_bar)
            .properties(background="transparent")
            .configure_view(strokeWidth=0, fill="transparent")
        )
        return chart

    @reactive.effect
    def _sync_top_neighborhood_click():
        selection = reactive_read(top_neighborhoods.widget.selections, "selected_bar")
        area_name = None

        if hasattr(selection, "value"):
            selection = selection.value

        if isinstance(selection, dict):
            area_name = selection.get(AREA)
            if isinstance(area_name, list) and area_name:
                area_name = area_name[0]
            elif not isinstance(area_name, str):
                value = selection.get("value")
                if isinstance(value, list) and value:
                    first = value[0]
                    if isinstance(first, dict):
                        area_name = first.get(AREA)
        elif isinstance(selection, list) and selection:
            first = selection[0]
            if isinstance(first, dict):
                area_name = first.get(AREA)

        if isinstance(area_name, str) and area_name in AREA_CHOICES:
            apply_area_selection(area_name)

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

    @reactive.effect
    async def _update_neighbourhood_map():
        df = map_df()
        active_area = selected_area.get()

        counts = dict(zip(df[AREA], df["permit_count"])) if not df.empty else {}
        max_count = int(df["permit_count"].max()) if not df.empty else 0

        features_out = []
        for feature in neighbourhood_geojson["features"]:
            area_name = feature["properties"]["name"]
            count = int(counts.get(area_name, 0))
            features_out.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "name": area_name,
                    "permit_count": count,
                    "fillColor": heat_fill_color(count, max_count),
                    "fillOpacity": 0.72 if count > 0 else 0.28,
                    "isSelected": area_name == active_area,
                },
            })

        tick_values = [max_count, max_count * 3 // 4, max_count // 2, max_count // 4, 0]
        tick_labels = [format_legend_tick(float(v)) for v in tick_values]

        await session.send_custom_message("update_nbhd_map", {
            "data": {"type": "FeatureCollection", "features": features_out},
            "bounds": INITIAL_MAP_BOUNDS,
            "tick_labels": tick_labels,
        })

    @reactive.effect
    @reactive.event(input.map_click)
    def _sync_map_click():
        try:
            area_name = input.map_click()
        except Exception:
            return
        if isinstance(area_name, str) and area_name in AREA_CHOICES:
            apply_area_selection(area_name)


app = App(app_ui, server)
