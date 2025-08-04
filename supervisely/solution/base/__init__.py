"""Foundational building blocks for *Supervisely Solution*.

This subpackage hosts low-level classes that power the visual solution graph
(SolutionElement, SolutionCardNode, …).  They were extracted from the legacy
``supervisely.solution.base_node`` module to improve maintainability.  The old
module continues to re-export these names for backward compatibility, but new
code should import directly from here.
"""

from __future__ import annotations

from .solution_element import SolutionElement
from .automation import Automation
from .automation_widget import AutomationWidget
from .solution_card_node import SolutionCardNode
from .solution_project_node import SolutionProjectNode

__all__: list[str] = [
    "SolutionElement",
    "Automation",
    "AutomationWidget",
    "SolutionCardNode",
    "SolutionProjectNode",
]