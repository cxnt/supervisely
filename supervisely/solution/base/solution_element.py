"""Implementation of :class:`~supervisely.solution.base.SolutionElement`."""

from __future__ import annotations

from typing import Dict

from supervisely.app import DataJson
from supervisely.app.widgets import Widget
from supervisely.app.widgets_context import JinjaWidgets

__all__: list[str] = ["SolutionElement"]


class SolutionElement(Widget):
    """Base class for every *Solution* element.

    Bridges *sly-app* widgets with :pyclass:`DataJson` to persist arbitrary
    state.  Subclasses **must** call ``super().__init__(widget_id=...)``.
    """

    def __new__(cls, *args, **kwargs):  # noqa: D401 – short description OK
        JinjaWidgets().incremental_widget_id_mode = True
        return super().__new__(cls)

    def __init__(self, *args, widget_id: str | None = None, **kwargs):
        if not hasattr(self, "widget_id"):
            self.widget_id = widget_id
        super().__init__(widget_id=self.widget_id)

    # ------------------------------------------------------------------
    # JSON helpers
    # ------------------------------------------------------------------

    def get_json_data(self) -> Dict:
        return {}

    def get_json_state(self) -> Dict:
        return {}

    def save_to_state(self, data: Dict) -> None:
        """Persist *data* inside :pyclass:`DataJson` under the widget's ID."""

        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")
        if self.widget_id not in DataJson():
            DataJson()[self.widget_id] = {}
        DataJson()[self.widget_id].update(data)
        DataJson().send_changes()