"""Compatibility wrapper for the :pyclass:`~VideoSampling` component.

The original implementation lives in :pymod:`supervisely.solution.components.video_samling`,
but the file name contained a typo ("samling").  New code SHOULD import
``VideoSampling`` from this module instead::

    from supervisely.solution.components.video_sampling import VideoSampling

The legacy module will be removed in a future major release.
"""

from __future__ import annotations

import warnings

# Re-export the original implementation while the old file name remains in the
# codebase for backward compatibility.
from .video_samling import VideoSampling as _VideoSampling  # type: ignore  # noqa: F401

__all__: list[str] = ["VideoSampling"]

# Public alias – the actual class comes from the legacy module.
VideoSampling = _VideoSampling  # noqa: N816 – keep original CamelCase naming convention

warnings.warn(
    "The module 'supervisely.solution.components.video_samling' is deprecated. "
    "Use 'supervisely.solution.components.video_sampling' instead.",
    DeprecationWarning,
    stacklevel=2,
)