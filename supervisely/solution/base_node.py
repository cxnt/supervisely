"""Base abstractions used by *Supervisely Solution* components.

The module provides several reusable building blocks that simplify construction
of interactive solution graphs:

* ``SolutionElement`` – common base class for widgets that cooperate with
  :pyclass:`SolutionGraph` and persist their state in :pyclass:`DataJson`.
* ``Automation`` / ``AutomationWidget`` – light wrapper around
  :pyclass:`~supervisely.solution.scheduler.TasksScheduler` that enables simple
  *run every N minutes* automations with a minimal UI.
* ``SolutionCardNode`` – thin adapter that binds a visual ``SolutionCard`` to a
  graph node and exposes helper methods for updating properties / badges.
* ``SolutionProjectNode`` – specialization for ``SolutionProject`` cards.

Only minor behavioural tweaks should be made here – the rest of the package
relies on the current public API.  The recent refactor focuses on improving
readability and making the intent of the code clearer without introducing
breaking changes.
"""

# NOTE: ``from __future__ import annotations`` helps with forward references in
# type annotations and avoids runtime import cycles.
from __future__ import annotations

from typing import Callable, Dict, List, Literal, Optional, Tuple, Union

from supervisely.api.project_api import ProjectInfo
from supervisely.app import DataJson
from supervisely.app.widgets import (
    Button,
    Checkbox,
    Container,
    Empty,
    InputNumber,
    Select,
    SolutionCard,
    SolutionGraph,
    SolutionProject,
    Text,
    Widget,
)
from supervisely.app.widgets_context import JinjaWidgets
from supervisely.solution.scheduler import TasksScheduler
from supervisely.solution.utils import get_seconds_from_period_and_interval

__all__ = [
    "SolutionElement",
    "Automation",
    "AutomationWidget",
    "SolutionCardNode",
    "SolutionProjectNode",
]

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Keys used for various status badges – extracted to named constants to avoid
# scattering magic strings throughout the code.
BADGE_KEY_AUTOMATION = "Automation"
BADGE_KEY_IN_PROGRESS = "⏳"
BADGE_KEY_FINISHED = "Finished"
BADGE_KEY_FAILED = "Failed"


class SolutionElement(Widget):
    """Base class for every *Solution* element.

    The class bridges `sly-app` *Widget* instances with :pyclass:`DataJson`,
    providing convenient helpers for persisting arbitrary state.  Subclasses
    **must** ensure they call ``super().__init__(widget_id=...)`` so that the
    underlying widget machinery is initialised correctly.
    """

    def __new__(cls, *args, **kwargs):
        # Enable *incremental_widget_id_mode* so that widgets created during the
        # lifetime of the app receive deterministic IDs.  This is important for
        # persisting their state across sessions.
        JinjaWidgets().incremental_widget_id_mode = True
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):  # noqa: D401 – short description OK
        """Instantiate the element and register it as a *Widget* instance."""

        widget_id = kwargs.get("widget_id", None)
        # Inherit `widget_id` if the subclass already defined it (via *dataclass*
        # or similar patterns) – otherwise fall back to the value from kwargs.
        if not hasattr(self, "widget_id"):
            self.widget_id = widget_id
        super().__init__(widget_id=self.widget_id)

    # ------------------------------------------------------------------
    # JSON helpers
    # ------------------------------------------------------------------

    def get_json_data(self) -> Dict:
        """Return default *data* section for front-end serialisation."""
        return {}

    def get_json_state(self) -> Dict:
        """Return default *state* section for front-end serialisation."""
        return {}

    def save_to_state(self, data: Dict) -> None:
        """Persist *data* inside :pyclass:`DataJson` under the widget's ID."""

        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")
        if self.widget_id not in DataJson():
            DataJson()[self.widget_id] = {}
        DataJson()[self.widget_id].update(data)
        DataJson().send_changes()


class Automation:  # noqa: D101 – simple mixin, docstring above
    @property
    def scheduler(self) -> TasksScheduler:  # noqa: D401 – simple property
        """Singleton instance of the background *TasksScheduler*."""

        return TasksScheduler()


class AutomationWidget(Automation):
    """Reusable widget that turns a function into a scheduled job."""

    def __init__(self, description: str, func: Callable):
        super().__init__()
        self.description = description
        self.func = func
        self.apply_btn = Button("Apply", plain=True, button_size="small")
        self.widget = self._create_widget()
        self.job_id = self.widget.widget_id
        self._on_apply: Optional[Callable[[], None]] = None

        @self.apply_btn.click  # noqa: D401 – inline callback definition
        def _on_apply_btn_click():  # pylint: disable=unused-variable
            self.apply()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def apply(self) -> None:
        """(Re)schedule the job using the current widget settings."""
        sec, _, _ = self.get_automation_details()
        if sec is None:
            if self.scheduler.is_job_scheduled(self.job_id):
                self.scheduler.remove_job(self.job_id)
        else:
            self.scheduler.add_job(self.func, sec, self.job_id, True)
        if self._on_apply is not None:
            self._on_apply()

    def on_apply(self, func: Callable) -> None:
        """Register a callback executed after *Apply* is pressed."""
        self._on_apply = func

    def is_enabled(self) -> bool:
        """Return *True* if the automation checkbox is ticked."""
        return self.enabled_checkbox.is_checked()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_widget(self) -> Container:  # noqa: C901 – acceptable complexity
        """Construct the UI for configuring the scheduler."""

        self.description = Text(self.description, status="text", color="gray")
        self.enabled_checkbox = Checkbox(content="Run every", checked=False)
        self.interval_input = InputNumber(
            min=1,
            value=60,
            debounce=1000,
            controls=False,
            size="mini",
            width=150,
        )
        self.interval_input.disable()
        self.period_select = Select(
            [
                Select.Item("min", "minutes"),
                Select.Item("h", "hours"),
                Select.Item("d", "days"),
            ],
            size="mini",
        )
        self.period_select.disable()

        settings_container = Container(
            [
                self.enabled_checkbox,
                self.interval_input,
                self.period_select,
                Empty(),
            ],
            direction="horizontal",
            gap=3,
            fractions=[1, 1, 1, 1],
            style="align-items: center",
            overflow="wrap",
        )

        apply_btn_container = Container([self.apply_btn], style="align-items: flex-end")

        # Enable / disable inputs depending on checkbox state.
        @self.enabled_checkbox.value_changed  # noqa: D401 – inline callback
        def _on_automate_checkbox_change(is_checked: bool):  # pylint: disable=unused-variable
            if is_checked:
                self.interval_input.enable()
                self.period_select.enable()
            else:
                self.interval_input.disable()
                self.period_select.disable()

        return Container([self.description, settings_container, apply_btn_container])

    # ------------------------------------------------------------------
    # State serialisation helpers
    # ------------------------------------------------------------------

    def get_automation_details(self) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """Return *seconds*, *interval*, *period* triple based on UI state."""

        enabled = self.enabled_checkbox.is_checked()
        period = self.period_select.get_value()
        interval = self.interval_input.get_value()

        if not enabled:
            return None, None, None  # Automation disabled.

        sec = get_seconds_from_period_and_interval(period, interval)
        if sec == 0:
            return None, None, None

        return sec, interval, period

    def save_automation_details(self, enabled: bool, interval: int, period: str) -> None:
        """Synchronise UI controls with stored scheduler settings."""

        if self.enabled_checkbox.is_checked() != enabled:
            self.enabled_checkbox.check() if enabled else self.enabled_checkbox.uncheck()
        if self.period_select.get_value() != period:
            self.period_select.set_value(period)
        if self.interval_input.get_value() != interval:
            self.interval_input.value = interval


# -----------------------------------------------------------------------------
# Graph nodes helpers
# -----------------------------------------------------------------------------

class SolutionCardNode(SolutionGraph.Node):  # noqa: D101 – docstring above
    """A :pyclass:`SolutionGraph` node backed by a ``SolutionCard`` widget."""

    def __new__(
        cls, content: Widget, x: int = 0, y: int = 0, *args, **kwargs
    ) -> SolutionGraph.Node:
        JinjaWidgets().incremental_widget_id_mode = True
        if not isinstance(content, (SolutionCard, SolutionProject)):
            raise TypeError("Content must be one of SolutionCard or SolutionProject")
        return super().__new__(cls, *args, **kwargs)

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def disable(self):
        self.content.disable()
        super().disable()

    def enable(self):
        self.content.enable()
        super().enable()

    # ------------------------------------------------------------------
    # Tooltip & badge helpers
    # ------------------------------------------------------------------

    def update_property(self, key: str, value: str, link: str | None = None, *, highlight: bool | None = None):
        for prop in self.content.tooltip_properties:
            if prop["key"] == key:
                self.content.update_property(key, value, link, highlight)
                return
        self.content.add_property(key, value, link, highlight)

    def remove_property_by_key(self, key: str):
        self.content.remove_property_by_key(key)

    # Badges -----------------------------------------------------------

    def update_badge(
        self,
        idx: int,
        label: str,
        *,
        on_hover: str | None = None,
        badge_type: Literal["info", "success", "warning", "error"] = "info",
    ):
        self.content.update_badge(idx, label, on_hover, badge_type)

    def update_badge_by_key(
        self,
        *,
        key: str,
        label: str,
        badge_type: Literal["info", "success", "warning", "error"] | None = None,
        new_key: str | None = None,
        plain: Optional[bool] = None,
    ):
        self.content.update_badge_by_key(
            key=key,
            label=label,
            new_key=new_key,
            badge_type=badge_type,
            plain=plain,
        )

    def add_badge(self, badge):
        self.content.add_badge(badge)

    def remove_badge(self, idx: int):
        self.content.remove_badge(idx)

    def remove_badge_by_key(self, key: str):
        self.content.remove_badge_by_key(key)

    # ------------------------------------------------------------------
    # Commonly used badge shortcuts
    # ------------------------------------------------------------------

    def _update_automation_badge(self, enable: bool) -> None:
        """Show or hide the \N{HIGH VOLTAGE SIGN} badge indicating automation."""

        for idx, prop in enumerate(self.content.badges):
            if prop["on_hover"] == BADGE_KEY_AUTOMATION:
                if not enable:
                    self.content.remove_badge(idx)
                return  # Badge already in correct state.

        if enable:
            self.content.add_badge(
                SolutionCard.Badge(
                    label="⚡",
                    on_hover=BADGE_KEY_AUTOMATION,
                    badge_type="warning",
                    plain=True,
                )
            )

    # Public helpers ---------------------------------------------------

    def show_automation_badge(self) -> None:
        """Display the *automation enabled* badge."""
        self._update_automation_badge(True)

    def hide_automation_badge(self) -> None:
        """Remove the *automation enabled* badge if present."""
        self._update_automation_badge(False)

    def show_in_progress_badge(self, *, key: str | None = None):
        """Mark the card as *in progress*."""
        key = key or BADGE_KEY_IN_PROGRESS
        self.content.update_badge_by_key(key=key, label="In progress", badge_type="info")

    def hide_in_progress_badge(self, *, key: str | None = None):
        """Clear the *in progress* marker."""
        key = key or BADGE_KEY_IN_PROGRESS
        self.content.remove_badge_by_key(key=key)

    def show_finished_badge(self):
        """Mark the card as *finished successfully*."""
        self.content.update_badge_by_key(key=BADGE_KEY_FINISHED, label="✅", plain=True, badge_type="success")

    def hide_finished_badge(self):
        self.content.remove_badge_by_key(key=BADGE_KEY_FINISHED)

    def show_failed_badge(self):
        """Mark the card as *failed*."""
        self.content.update_badge_by_key(key=BADGE_KEY_FAILED, label="❌", plain=True, badge_type="error")

    def hide_failed_badge(self):
        self.content.remove_badge_by_key(key=BADGE_KEY_FAILED)


class SolutionProjectNode(SolutionCardNode):
    """A ``SolutionCardNode`` specialised for *Solution Project* cards."""

    def __new__(
        cls, content: Widget, x: int = 0, y: int = 0, *args, **kwargs
    ) -> SolutionGraph.Node:  # noqa: D401 – simple override
        if not isinstance(content, SolutionProject):
            raise TypeError("Content must be an instance of SolutionProject")
        return super().__new__(cls, content, x, y, *args, **kwargs)

    # ------------------------------------------------------------------
    # Project-specific helpers
    # ------------------------------------------------------------------

    def update_preview(self, imgs: List[str], counts: List[int]):
        self.content.update_preview_url(imgs)
        self.content.update_items_count(counts)

    def update(
        self,
        *,
        project: ProjectInfo | None = None,
        new_items_count: int | None = None,
        urls: List[Union[int, str, None]] | None = None,
        counts: List[Union[int, None]] | None = None,
    ):
        if project is not None:
            self.project = project
        if new_items_count is not None:
            self.update_property(key="Last update", value=f"+{new_items_count}")
            self.update_property(key="Total", value=f"{self.project.items_count} images")
            self.update_badge_by_key(key="Last update:", label=f"+{new_items_count}")

        if getattr(self, "is_training", False) and urls is not None and counts is not None:
            self.update_preview(urls, counts)
        else:
            self.update_preview(
                [self.project.image_preview_url],
                [self.project.items_count],
            )
