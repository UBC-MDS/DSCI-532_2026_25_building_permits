# Changelog

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
