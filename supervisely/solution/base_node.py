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

# NOTE: This file became a thin compatibility layer after refactor that moved
# each class to its own module inside ``supervisely.solution.base``.  Keeping
# these re-exports allows legacy imports ::
#
#     from supervisely.solution.base_node import SolutionElement
#
# to continue working without modification.  New code SHOULD import from the
# ``supervisely.solution.base`` package directly.

"""DEPRECATED – use :pymod:`supervisely.solution.base` instead."""

from __future__ import annotations

import warnings

# Re-export moved classes ---------------------------------------------------

from .base.solution_element import SolutionElement  # noqa: F401
from .base.automation import Automation  # noqa: F401
from .base.automation_widget import AutomationWidget  # noqa: F401
from .base.solution_card_node import SolutionCardNode  # noqa: F401
from .base.solution_project_node import SolutionProjectNode  # noqa: F401

__all__: list[str] = [
    "SolutionElement",
    "Automation",
    "AutomationWidget",
    "SolutionCardNode",
    "SolutionProjectNode",
]

# Emit deprecation notice on first import.
warnings.warn(
    "`supervisely.solution.base_node` is deprecated. "
    "Import classes from `supervisely.solution.base` instead.",
    DeprecationWarning,
    stacklevel=2,
)
