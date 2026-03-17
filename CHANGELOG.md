# Changelog

## [0.4.0] - 2026-03-17

### Added

- Interactive cross-filtering: clicking a neighbourhood on the map or the top neighbourhoods bar chart filters the other views (PR #90)
- Heatmap coloring on neighbourhood map polygons to show relative permit counts, with a colour legend (PR #91)
- Tooltip on the Permit Volume Over Time chart showing month and permit count on hover (PR #86)
- "No filters selected" empty state banner when all work type checkboxes are unchecked (PR #87)
- Lazy loading with Ibis and DuckDB for faster dashboard filter performance; data converted to Parquet format (PRs #81, #83)
- Playwright end-to-end tests for the app (PR #94)
- Unit tests for refactored utility functions with pytest (PR #95)
- Testing instructions added to README

### Changed

- Neighbourhood map rebuilt from ipyleaflet to pure Leaflet.js for better rendering and heatmap support (PR #91, #92)
- Value box cards made significantly more compact: reduced min-height, font sizes, icon sizes, and padding; text centered across full card width (PR #85)
- X-axis labels on Permit Volume Over Time chart fixed to show years (monthly when time range is short) instead of April/October (PR #88)
- Refactored `get_unique_sorted` and `compute_avg_days` into `src/utils.py` for better code organization (PR #95)
- Updated `reports/m2_spec.md` to include advanced feature documentation (PR #90)

### Fixed

- Value boxes were inflated to 240px by a general card CSS rule; overridden with `min-height: auto` for value boxes only (PR #85)
- X-axis labelling bug showing month names instead of years on the permit volume chart (PR #88)
- Blank map issue resolved with adjusted zoom and positioning (PR #92)
- Utils import path fix (PR #96)

### Reflection

Milestone 4 focused on addressing instructor and peer feedback, improving code quality, and adding an advanced interactive feature. The two critical visual bugs (value card height and x-axis labelling) were resolved first. The map was rebuilt from ipyleaflet to pure Leaflet.js to support heatmap polygon coloring, which was a significant refactor but resulted in better geographic visualization. The advanced feature (cross-filtering between the map and bar chart via click events) adds a coordinated view interaction pattern that was not in the original plan but improves the exploratory workflow. On the engineering side, the data loading was migrated to Ibis + DuckDB with Parquet files for better performance, utility functions were extracted and tested, and Playwright end-to-end tests were added to catch regressions. Non-critical feedback items addressed include the permit volume tooltip and the empty state message for cleared filters. Remaining non-critical items (N1 summary text, N2/N3 AI tab layout, N6 multi-select, N7 hover tooltips) were deprioritized in favour of the testing and advanced feature requirements.

A Playwright test suite was implemented, examples below. Full implementations are documented in `test_app_playwright.py`
test_initial_value_boxes_non_empty()
- Value boxes render with non-empty values on load
- Ensures reactive chains correctly fire on startup
test_initial_avg_days_format()
- Avg Processing Time box correctly renders as '<number> Days'
- A format change would break the value-box label
test_neighbourhood_filter_updates_avg_days()
- Selecting a single neighbourhood updates Avg Processing Time
- Ensures the avg_days reactive re-fires when the area filter changes
test_date_range_boundary_permits_are_included()
- Setting the same start and end dates returns the permits
- Ensures the filter is inclusive on both ends

## [0.3.0] - 2026-02-12

### Added

- QueryChat AI tab with natural language data filtering powered by Anthropic Claude (PR #57)
- Permit volume over time and top neighbourhoods charts in the AI tab, driven by QueryChat-filtered data (PR #61)
- Download button to export AI-filtered data as CSV (PR #62)
- GeoJSON neighbourhood boundaries on the map with hover tooltips showing area name and permit count (PR #60)
- Searchable neighbourhood dropdown using selectize with type-to-search (PR #60)
- Auto-zoom on the map to fit filtered or selected neighbourhoods (PR #60)

### Changed

- Neighbourhood map now renders GeoJSON polygon boundaries instead of circle markers, giving a clearer view of geographic areas
- Neighbourhood dropdown upgraded from a plain select to a selectize input with search and auto-clear behaviour
- Map highlights the selected neighbourhood with a distinct border style and zooms to fit its bounds
- AI tab layout reorganised into a top row (chat and filtered table) and a bottom row (two reactive charts)

### Reflection

Milestone 3 focused on adding an AI-powered exploration layer to the dashboard. The main addition is the QueryChat tab, which lets users filter the permit dataset using natural language queries instead of manual sidebar controls. Two charts in the AI tab (permit volume over time and top neighbourhoods) update reactively based on the chat-filtered dataframe, and a download button lets users export the result as a CSV. On the Dashboard tab, the neighbourhood map was upgraded from simple circle markers to GeoJSON polygon boundaries with hover tooltips and auto-zoom, which makes the geographic context much clearer. The neighbourhood dropdown was also replaced with a searchable selectize input.

The main deviation from the original plan was the scope of the AI integration. The initial plan did not include a chatbot-driven filtering interface; this was added in response to the Milestone 3 requirement for a QueryChat component. The GeoJSON map upgrade was also not in the original sketch but was a natural improvement once the boundary data became available.

Known limitations include the dependency on an external API key (Anthropic) for the AI tab, which means the tab will not function without a valid key in the `.env` file. The AI-generated SQL filters depend on the LLM interpreting the user's query correctly, so edge cases in phrasing may produce unexpected results. The download button exports whatever the current AI-filtered state is, so users need to verify the filter before exporting.

The dashboard continues to follow the visualization best practices from DSCI 531. Chart types match the comparison tasks (line chart for temporal trends, bar chart for categorical ranking, choropleth-style map for geographic distribution), labels and titles are clear, and the layout groups related views together. We do not believe there are intentional deviations from those practices in this version.

## [0.2.0] - 2026-02-28

### Added

- Interactive neighbourhood permit map built with `ipyleaflet`
- Permit volume over time chart built with `altair`
- Top neighbourhoods by permit volume bar chart
- Value boxes with icons for Permits Issued and Avg Processing Time
- Sidebar filters for date range, work type, and neighbourhood
- Reset Filters button to restore the default filter state
- Top N slider for the neighbourhood ranking chart
- `faicons` dependency for value box icons

### Changed

- Redesigned the dashboard with a modern CSS layout, gradient accents, and updated card styling
- Reorganized the page so the two value boxes sit at the top and the permit volume over time chart occupies its own full row below them
- Improved responsive behavior for tablet and mobile screen sizes
- Styled value boxes with stronger visual hierarchy and showcase icons
- Updated the default work type selection to show all permit types on initial load and after reset

### Fixed

- Checkbox text alignment in the sidebar
- Reset button behavior so filters restore correctly
- Empty-state handling when no permit types are selected

### Reflection

At this stage, the job board summary in [reports/m2_spec.md](./reports/m2_spec.md) shows that job stories `#1` to `#5` and `#7` are implemented. These cover the interactive neighbourhood map, the average processing time summary, reactive filtering across the dashboard, the total permits issued metric, the reset button, and the top neighbourhoods by permit volume chart. Together, these implemented stories support the main exploration workflow in the app: users can filter by date, work type, and neighbourhood, then compare summary metrics and neighbourhood-level activity across coordinated views. Job story `#6`, the permit volume over time view with a forecast, is still marked as in progress on the board. The current app includes the permit volume over time chart itself, but the forecast portion described in that story remains unimplemented relative to the original idea. Overall, the main views from the proposal and sketch are present, deployed, and documented, with the forecast component as the main remaining gap.

The main deviations from the original plan were layout and default-state changes. The interface moved from a simpler layout to a more polished CSS redesign with stronger visual grouping, gradients, icons, and a more responsive arrangement for smaller screens. More specifically, the two value boxes were positioned together at the top of the dashboard to surface the highest-level summary metrics first, and the permit volume over time chart was given its own full row beneath them so the trend line has more horizontal space and is easier to read. We also revisited the work type default behavior. An earlier version started with no work types selected, but this was changed to select all types by default so the app shows data immediately on load and after reset. These changes were made to improve clarity and usability rather than to expand scope.

Some known edge cases include situations where the selected filters produce very little or no data. If the user manually clears all work types, the app returns no matching rows rather than failing, which is expected behavior but can make the dashboard appear empty. Selecting a single neighbourhood also narrows the map and the top neighbourhoods chart to that one area only. In those cases, the outputs may look sparse or less informative, but they still correctly reflect the filtered data rather than indicating a broken visualization.

To our knowledge, the dashboard follows the visualization best practices emphasized in DSCI 531. We aimed to use clear labels,readable layouts, and chart choices that match the underlying comparisons being shown. We do not believe there are any intentional deviations from those best practices in the current version.

The strongest parts of the current version are the reactive filtering flow, the integration of multiple coordinated views, and the improved layout. The main limitations are that the app still has relatively simple empty-state messaging, limited explanatory annotation, and no forecast component yet in the permit volume over time view. Future improvements would include clearer no-data messages, richer tooltips, accessibility refinements, additional tests around filter interactions, and implementation of the forecast feature described in the original plan.
