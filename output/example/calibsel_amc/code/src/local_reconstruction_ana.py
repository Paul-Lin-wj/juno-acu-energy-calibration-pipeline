# -----------------------------------------------------------------------------
# local_reconstruction_ana.py
# 逐行摘自 reconstruction_ana 0.2.0 的 LocalUtils.py（作者 Shubing Liu）：
#   /workfs2/juno/shubingliu/my_python_pkg/reconstruction_ana_pkg/
#   reconstruction_ana/LocalUtils.py
# 摘取内容：GetBinCenter / find_groups / getCoinTag / HistBasedLimitFinding
#   （correlation_analyzer.py 与 fv_selector.py 实际用到的全部函数）
# 改动：无 —— 函数体逐字节原样；仅文件头注释为本模块所加。
# 先例：esd2npz/src/local_utils.py 同样摘自该包（见 esd2npz/PROVENANCE.md）。
# -----------------------------------------------------------------------------
import numpy as np
import awkward as ak
import numba


def GetBinCenter(bins):
    """Return bin centers from bin edges."""
    return (bins[:-1] + bins[1:]) / 2


@numba.jit(nopython=True)
def find_groups(time_arr, cut_limit):
    """
    Group consecutive events whose time differences are below *cut_limit*.
    Returns (tags, group_starts, group_ends).
    """
    tags = np.zeros_like(time_arr, dtype=np.int64)
    group_starts = []
    group_ends = []

    i = 0
    while i < len(time_arr):
        start_index = i
        while i + 1 < len(time_arr) and time_arr[i + 1] - time_arr[i] < cut_limit:
            i += 1
        group_size = i - start_index + 1
        for j in range(start_index, i + 1):
            tags[j] = group_size
        group_starts.append(start_index)
        group_ends.append(i + 1)
        i += 1

    return tags, group_starts, group_ends


def getCoinTag(energy_arr, time_arr, cut_limit):
    """
    Coincidence tagging: group events by time proximity.
    Returns dict with n_coince, energy_groups, time_groups, index.
    """
    _, group_starts, group_ends = find_groups(time_arr, cut_limit)

    energy_groups = []
    time_groups = []
    indices = []
    unique_tags = []

    for start, end in zip(group_starts, group_ends):
        energy_groups.append(energy_arr[start:end])
        time_groups.append(time_arr[start:end])
        indices.append(list(range(start, end)))
        unique_tags.append(end - start)

    result_dict = {
        "n_coince": unique_tags,
        "energy_groups": ak.Array(energy_groups),
        "time_groups": ak.Array(time_groups),
        "index": ak.Array(indices),
    }
    return result_dict


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
        x_cross_positive = x_positive[np.min(true_index)] if true_index.size > 0 else max(x_values)
        if direction == "right":
            return start_point, x_cross_positive

    if direction in ["left", "both"]:
        x_negative = x_values[x_values < start_point]
        y_negative = y_values[x_values < start_point]
        true_index = np.where(y_negative < threshold)[0]
        x_cross_negative = x_negative[np.max(true_index)] if true_index.size > 0 else min(x_values)
        if direction == "left":
            return start_point, x_cross_negative

    if direction == "both":
        return start_point, x_cross_negative, x_cross_positive


# correlation_analyzer.py 的 import 行还引用了 PlotFitResult；本流程未调用，
# 提供与原包同名同签名的占位以保持 import 兼容（不会被走到）。
def PlotFitResult(*args, **kwargs):
    raise NotImplementedError(
        "PlotFitResult is imported by correlation_analyzer.py but not used "
        "in this pipeline; see local_reconstruction_ana.py header.")
