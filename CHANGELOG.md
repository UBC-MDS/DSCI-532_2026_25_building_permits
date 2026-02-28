# Changelog

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
