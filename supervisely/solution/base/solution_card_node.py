"""Graph node backed by a :class:`supervisely.app.widgets.SolutionCard`."""

from __future__ import annotations

from typing import List, Literal, Optional, Union

from supervisely.app.widgets import SolutionCard, SolutionGraph, SolutionProject, Widget
from supervisely.app.widgets_context import JinjaWidgets

__all__: list[str] = ["SolutionCardNode"]

# Common badge keys – avoid scattering magic strings.
BADGE_KEY_AUTOMATION = "Automation"
BADGE_KEY_IN_PROGRESS = "⏳"
BADGE_KEY_FINISHED = "Finished"
BADGE_KEY_FAILED = "Failed"


class SolutionCardNode(SolutionGraph.Node):
    """Thin adapter that binds a visual card to a graph node."""

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
    # Common badge shortcuts
    # ------------------------------------------------------------------

    def _update_automation_badge(self, enable: bool) -> None:
        for idx, prop in enumerate(self.content.badges):
            if prop["on_hover"] == BADGE_KEY_AUTOMATION:
                if not enable:
                    self.content.remove_badge(idx)
                return
        if enable:
            self.content.add_badge(
                SolutionCard.Badge(
                    label="⚡",
                    on_hover=BADGE_KEY_AUTOMATION,
                    badge_type="warning",
                    plain=True,
                )
            )

    def show_automation_badge(self) -> None:
        self._update_automation_badge(True)

    def hide_automation_badge(self) -> None:
        self._update_automation_badge(False)

    def show_in_progress_badge(self, *, key: str | None = None):
        key = key or BADGE_KEY_IN_PROGRESS
        self.content.update_badge_by_key(key=key, label="In progress", badge_type="info")

    def hide_in_progress_badge(self, *, key: str | None = None):
        key = key or BADGE_KEY_IN_PROGRESS
        self.content.remove_badge_by_key(key=key)

    def show_finished_badge(self):
        self.content.update_badge_by_key(
            key=BADGE_KEY_FINISHED, label="✅", plain=True, badge_type="success"
        )

    def hide_finished_badge(self):
        self.content.remove_badge_by_key(key=BADGE_KEY_FINISHED)

    def show_failed_badge(self):
        self.content.update_badge_by_key(
            key=BADGE_KEY_FAILED, label="❌", plain=True, badge_type="error"
        )

    def hide_failed_badge(self):
        self.content.remove_badge_by_key(key=BADGE_KEY_FAILED)