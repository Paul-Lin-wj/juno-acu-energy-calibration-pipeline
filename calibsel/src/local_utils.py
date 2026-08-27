"""
local_utils.py
==============
Small analysis utilities inlined from the external `reconstruction_ana`
package (Shubing Liu, /workfs2/juno/shubingliu/my_python_pkg/reconstruction_ana_pkg,
version 0.2.0, LocalUtils.py) so that this project has no dependency on that
package (and on its numba/awkward/psutil requirements).

Only the four functions actually used by combine_selection.py are inlined:
  - GetBinCenter
  - get_memory_usage
  - save_arrays_to_text
  - HistBasedLimitFinding
"""

from __future__ import annotations

import numpy as np


def GetBinCenter(bins):
    """Return bin centers from bin edges."""
    return (np.asarray(bins)[:-1] + np.asarray(bins)[1:]) / 2


def get_memory_usage():
    """Print current process memory usage in MB (falls back to /proc)."""
    import os

    try:
        import psutil  # optional

        process = psutil.Process(os.getpid())
        print(f"Memory usage: {process.memory_info().rss / (1024 ** 2):.2f} MB")
        return
    except ImportError:
        pass
    try:
        with open(f"/proc/{os.getpid()}/statm") as f:
            pages = int(f.read().split()[1])
        print(f"Memory usage: {pages * 4096 / (1024 ** 2):.2f} MB")
    except Exception:
        print("Memory usage: <unavailable>")


def save_arrays_to_text(concat_sec, concat_naosec, output_file="output.txt"):
    """Save two arrays (seconds and nanoseconds) to a text file, one pair per line."""
    if len(concat_sec) != len(concat_naosec):
        raise ValueError("The two arrays must be of the same length")
    with open(output_file, "w") as f:
        for sec, nsec in zip(concat_sec, concat_naosec):
            f.write(f"{sec},{nsec}\n")


def HistBasedLimitFinding(
    x_values,
    y_values,
    threshold,
    direction="right",
    start_point=None,
):
    """
    Find the crossing point(s) where y drops below *threshold*.
    Direction: 'left', 'right', or 'both'.
    """
    x_values = np.asarray(x_values)
    y_values = np.asarray(y_values)

    if (start_point is None) and direction == "both":
        start_point = x_values[np.argmax(y_values)]
    elif (start_point is None) and direction in ["left", "right"]:
        start_point = 0

    if direction in ["right", "both"]:
        x_positive = x_values[x_values > start_point]
        y_positive = y_values[x_values > start_point]
        true_index = np.where(y_positive < threshold)[0]
        x_cross_positive = (
            x_positive[np.min(true_index)] if true_index.size > 0 else max(x_values)
        )
        if direction == "right":
            return start_point, x_cross_positive

    if direction in ["left", "both"]:
        x_negative = x_values[x_values < start_point]
        y_negative = y_values[x_values < start_point]
        true_index = np.where(y_negative < threshold)[0]
        x_cross_negative = (
            x_negative[np.max(true_index)] if true_index.size > 0 else min(x_values)
        )
        if direction == "left":
            return start_point, x_cross_negative

    if direction == "both":
        return start_point, x_cross_negative, x_cross_positive
