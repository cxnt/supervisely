"""Specialised node for :class:`~supervisely.app.widgets.SolutionProject` cards."""

from __future__ import annotations

from typing import List, Union

from supervisely.api.project_api import ProjectInfo
from supervisely.app.widgets import SolutionProject, Widget

from .solution_card_node import (
    BADGE_KEY_FINISHED,
    BADGE_KEY_IN_PROGRESS,
    SolutionCardNode,
)

__all__: list[str] = ["SolutionProjectNode"]


class SolutionProjectNode(SolutionCardNode):
    """A `SolutionCardNode` tailored to handle project-specific visuals."""

    def __new__(
        cls, content: Widget, x: int = 0, y: int = 0, *args, **kwargs
    ) -> "SolutionProjectNode":
        if not isinstance(content, SolutionProject):
            raise TypeError("Content must be an instance of SolutionProject")
        return super().__new__(cls, content, x, y, *args, **kwargs)

    # ------------------------------------------------------------------
    # Project helpers
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
            self.update_preview(imgs=urls, counts=counts)
        else:
            self.update_preview(
                imgs=[self.project.image_preview_url],
                counts=[self.project.items_count],
            )