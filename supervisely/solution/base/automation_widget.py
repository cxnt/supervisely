"""UI helper turning a callable into a scheduled job."""

from __future__ import annotations

from typing import Callable, Optional, Tuple

from supervisely.app.widgets import (
    Button,
    Checkbox,
    Container,
    Empty,
    InputNumber,
    Select,
    Text,
)
from supervisely.solution.utils import get_seconds_from_period_and_interval

from .automation import Automation

__all__: list[str] = ["AutomationWidget"]


class AutomationWidget(Automation):
    """Reusable widget that lets the user schedule *func* at regular intervals."""

    def __init__(self, description: str, func: Callable):
        super().__init__()
        self.description = description
        self.func = func

        # Internal state -------------------------------------------------
        self._on_apply: Optional[Callable[[], None]] = None

        # UI -------------------------------------------------------------
        self.apply_btn = Button("Apply", plain=True, button_size="small")
        self.widget = self._build_widget()
        self.job_id = self.widget.widget_id

        @self.apply_btn.click  # noqa: D401 – inline callback definition
        def _apply():  # pylint: disable=unused-variable
            self.apply()

    # ------------------------------------------------------------------
    # Scheduler interaction
    # ------------------------------------------------------------------

    def apply(self) -> None:
        """(Re)schedule the job using current settings."""
        sec, _, _ = self._get_settings()
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
        return self.enabled_checkbox.is_checked()

    # ------------------------------------------------------------------
    # UI construction & state helpers
    # ------------------------------------------------------------------

    def _build_widget(self) -> Container:
        """Return container with description, controls and apply button."""

        self.description = Text(self.description, status="text", color="gray")
        self.enabled_checkbox = Checkbox("Run every", checked=False)
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

        apply_container = Container([self.apply_btn], style="align-items: flex-end")

        @self.enabled_checkbox.value_changed  # noqa: D401 – inline callback
        def _toggle(is_checked: bool):  # pylint: disable=unused-variable
            controls = [self.interval_input, self.period_select]
            for ctrl in controls:
                ctrl.enable() if is_checked else ctrl.disable()

        return Container([self.description, settings_container, apply_container])

    # ------------------------------------------------------------------
    # Settings serialisation
    # ------------------------------------------------------------------

    def _get_settings(self) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        enabled = self.enabled_checkbox.is_checked()
        period = self.period_select.get_value()
        interval = self.interval_input.get_value()

        if not enabled:
            return None, None, None

        sec = get_seconds_from_period_and_interval(period, interval)
        if sec == 0:
            return None, None, None
        return sec, interval, period

    def save_settings(self, *, enabled: bool, interval: int, period: str) -> None:
        """Synchronise UI controls with stored scheduler settings."""

        self.enabled_checkbox.check() if enabled else self.enabled_checkbox.uncheck()
        self.period_select.set_value(period)
        self.interval_input.value = interval