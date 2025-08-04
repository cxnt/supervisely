"""Simple mixin providing access to the global :pyclass:`TasksScheduler`."""

from __future__ import annotations

from supervisely.solution.scheduler import TasksScheduler

__all__: list[str] = ["Automation"]


class Automation:
    """Mixin that exposes :pyattr:`scheduler` property."""

    @property
    def scheduler(self) -> TasksScheduler:  # noqa: D401 – simple property
        return TasksScheduler()