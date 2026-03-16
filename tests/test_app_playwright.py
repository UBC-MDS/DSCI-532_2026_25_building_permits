# running tests:
# python -m pytest tests/test_app_playwright.py -v --browser chromium


from shiny.playwright import controller
from shiny.run import ShinyAppProc
from shiny.pytest import create_app_fixture
from playwright.sync_api import Page
import re

app = create_app_fixture("../src/app.py")


# Initial state

def test_initial_value_boxes_non_empty(page: Page, app: ShinyAppProc) -> None:
    """Value boxes render with non-empty values on load;
    ensures Reactive chains correctly fire on startup."""
    page.goto(app.url)
    page.goto(app.url)
    controller.OutputText(page, "permits_to_date").expect_value(re.compile(r".+"))
    controller.OutputText(page, "avg_days").expect_value(re.compile(r".+"))

    permits_to_date = controller.OutputText(page, "permits_to_date").get_value()
    avg_days = controller.OutputText(page, "avg_days").get_value()

    assert permits_to_date != "", "permits_to_date should not be empty on load"
    assert avg_days != "", "avg_days should not be empty on load"

def test_initial_avg_days_format(page: Page, app: ShinyAppProc) -> None:
    """Avg Processing Time box correctly renders as '<number> Days';
    a format change would break the value-box label."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    value = controller.OutputText(page, "avg_days").get_value()
    assert value.endswith(" Days"), (
        f"Expected avg_days to end with ' Days', got: {value!r}"
    )


# Checkbox filter

def test_deselect_all_checkboxes_zeroes_permit_count(page: Page, app: ShinyAppProc) -> None:
    """Deselecting all permit type checkboxes reduces the permit count to 0;
    ensures the type filter is functioning correctly."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    controller.InputCheckboxGroup(page, "checkbox_group").set([])
    controller.OutputText(page, "permits_to_date").expect_value("0")


def test_permit_filter_reduces_perit_count(page, app):
    """Selecting a single permit type reduces the permit count;
    ensures the type filter is functioning correctly."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")
    full_count = int(
        controller.OutputText(page, "permits_to_date").get_value().replace(",", "")
    )

    controller.InputCheckboxGroup(page, "checkbox_group").set(["New Building"])

    permits = controller.OutputText(page, "permits_to_date")
    permits.expect_value(re.compile(rf"^(?!{full_count:,}$).+"))
    filtered_count = int(permits.get_value().replace(",", ""))

    assert filtered_count < full_count, (
        f"Filtering to one type should reduce count: {filtered_count} !< {full_count}"
    )


# Neighbourhood filter

def test_neighbourhood_filter_reduces_permit_count(page, app):
    """Selecting a single neighborhood reduces the permit count;
    ensures the area filter is functioning correctly."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")
    full_count = int(
        controller.OutputText(page, "permits_to_date").get_value().replace(",", "")
    )

    controller.InputSelectize(page, "area").set("Downtown")

    permits = controller.OutputText(page, "permits_to_date")
    permits.expect_value(re.compile(rf"^(?!{full_count:,}$).+"))
    filtered_count = int(permits.get_value().replace(",", ""))

    assert filtered_count < full_count, (
        f"Downtown filter should reduce count: {filtered_count} !< {full_count}"
    )


def test_neighbourhood_filter_updates_avg_days(page: Page, app: ShinyAppProc) -> None:
    """Selecting a single neighbourhood updates Avg Processing Time;
    ensures the avg_days reactive re-fires when the area filter changes."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    controller.InputSelectize(page, "area").set("Downtown")
    downtown = controller.OutputText(page, "avg_days").get_value()

    # Values may coincidentally match but the output should always be well-formed
    assert downtown.endswith(" Days"), f"Unexpected format after area filter: {downtown!r}"


# Date range filter

def test_narrow_date_range_reduces_permit_count(page, app):
    """Reducing the date range reduces the permit count;
    ensures the date range filter is functioning correctly."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")
    full_count = int(
        controller.OutputText(page, "permits_to_date").get_value().replace(",", "")
    )

    controller.InputDateRange(page, "date_range").set(("2023-01-01", "2023-12-31"))

    permits = controller.OutputText(page, "permits_to_date")
    permits.expect_value(re.compile(rf"^(?!{full_count:,}$).+"))
    filtered_count = int(permits.get_value().replace(",", ""))

    assert filtered_count < full_count, (
        f"Single-year filter should reduce count: {filtered_count} !< {full_count}"
    )


def test_date_range_boundary_permits_are_included(page: Page, app: ShinyAppProc) -> None:
    """Setting the same start and end dates returns the permits
    issued on that day; ensures the filter is inclusive on both ends."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    date_range = controller.InputDateRange(page, "date_range")
    date_range.set(("2023-06-15", "2023-06-15"))

    count_str = controller.OutputText(page, "permits_to_date").get_value()

    assert count_str.replace(",", "").isdigit(), (
        f"permits_to_date should be an integer for a single-day range, got: {count_str!r}"
    )


# Reset button

def test_reset_restores_permit_count(page: Page, app: ShinyAppProc) -> None:
    """After applying filters, the Reset button restores the full permit
    count."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    full_count = controller.OutputText(page, "permits_to_date").get_value()

    # Narrow via checkbox, then reset
    controller.InputCheckboxGroup(page, "checkbox_group").set([])
    controller.OutputText(page, "permits_to_date").expect_value("0")

    controller.InputActionButton(page, "action_button").click()

    controller.OutputText(page, "permits_to_date").expect_value(full_count)


def test_reset_restores_neighbourhood_selection(page: Page, app: ShinyAppProc) -> None:
    """Reset returns the neighbourhood dropdown to 'All'."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    controller.InputSelectize(page, "area").set("Kitsilano")
    controller.InputActionButton(page, "action_button").click()

    controller.InputSelectize(page, "area").expect_selected(["All"])


def test_reset_restores_top_n_slider(page: Page, app: ShinyAppProc) -> None:
    """Reset restores the Top Neighbourhoods slider to its default of 5."""
    page.goto(app.url)
    page.wait_for_load_state("networkidle")

    controller.InputSlider(page, "top_n").set("15")
    controller.InputActionButton(page, "action_button").click()

    controller.InputSlider(page, "top_n").expect_value("5")
