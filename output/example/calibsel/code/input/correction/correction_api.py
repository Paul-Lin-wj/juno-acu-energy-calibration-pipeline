#!/usr/bin/env python3
"""
correction_api.py
Author: Shubing Liu <liusb@ihep.ac.cn>
Created on 2026-06-10
Description:
    Reusable 26B r-bias, Po214 spatial non-uniformity, v2 time-stability, and
    absolute energy-scale correction API.
Usage:
    from correction_api import EnergyCorrection26B
    corr = EnergyCorrection26B()
    energy_corr, x_corr, y_corr, z_corr = corr.correct(
        energy, x, y, z, event_time, run, position_unit="mm"
    )
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import BSpline


ABSOLUTE_ENERGY_SCALE_BY_PHASE = {
    1: 0.99340419,
    2: 0.99340419,
    3: 0.99743135,
    4: 0.99743135,
}


class EnergyCorrection26B:
    """Apply vertex r-bias, spatial energy, time energy, and absolute scale."""

    def __init__(self, data_dir=None, absolute_scale_by_phase=None):
        self.data_dir = Path(data_dir) if data_dir is not None else Path(__file__).resolve().parent / "data"
        scales = dict(absolute_scale_by_phase or ABSOLUTE_ENERGY_SCALE_BY_PHASE)
        if set(scales) != {1, 2, 3, 4}:
            raise ValueError("absolute_scale_by_phase must define phases 1, 2, 3, and 4")
        self.absolute_scale_by_phase = {
            phase: float(scales[phase]) for phase in (1, 2, 3, 4)
        }
        self.vertex_radius_mm, self.vertex_bias_mm = self._load_vertex_table(
            self.data_dir / "vertex_correction_26B.csv"
        )
        self.time_t, self.time_scale = self._load_time_curve(
            self.data_dir / "time_correction_v2.csv"
        )
        self.phase_ranges = self._load_phase_ranges(
            self.data_dir / "ValProd26BPhase.csv"
        )
        self.models = {
            phase: self._load_spatial_model(
                self.data_dir / f"phase{phase}_model.npz"
            )
            for phase in (1, 2, 3, 4)
        }

    @staticmethod
    def _load_vertex_table(path):
        frame = pd.read_csv(path)
        order = np.argsort(frame["r_reco_mm"].to_numpy(dtype=np.float64))
        radius = frame["r_reco_mm"].to_numpy(dtype=np.float64)[order]
        bias = frame[
            "merged_smooth_bias_r_rec_minus_r_true_mm"
        ].to_numpy(dtype=np.float64)[order]
        return radius, bias

    @staticmethod
    def _load_time_curve(path):
        frame = pd.read_csv(path)
        order = np.argsort(frame["timestamp"].to_numpy(dtype=np.float64))
        return (
            frame["timestamp"].to_numpy(dtype=np.float64)[order],
            frame["scale_factor"].to_numpy(dtype=np.float64)[order],
        )

    @staticmethod
    def _load_phase_ranges(path):
        ranges = []
        with Path(path).open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                phase_text = row.get("ValProd26B") or next(iter(row.values()))
                run_range = row.get("Run Range") or list(row.values())[1]
                phase = int(re.search(r"(\d+)", phase_text).group(1))
                run_min, run_max = map(int, str(run_range).split("-"))
                ranges.append((phase, run_min, run_max))
        if not ranges:
            raise ValueError(f"No phase ranges found in {path}")
        return ranges

    @staticmethod
    def _load_spatial_model(path):
        if not path.exists():
            raise FileNotFoundError(path)
        with np.load(path) as data:
            return {
                "coefficient": np.asarray(data["coefficient"], dtype=np.float64),
                "x_knots": np.asarray(data["x_knots"], dtype=np.float64),
                "y_knots": np.asarray(data["y_knots"], dtype=np.float64),
                "degree": int(data["degree"]),
                "r3_min": float(data["r3_min"]),
                "r3_max": float(data["r3_max"]),
                "costheta_min": float(data["costheta_min"]),
                "costheta_max": float(data["costheta_max"]),
                "target_mev": float(data["target_mev"]),
            }

    def phase_from_run(self, run):
        runs = np.atleast_1d(np.asarray(run, dtype=np.int64))
        phases = np.empty(len(runs), dtype=np.int64)
        for index, run_id in enumerate(runs):
            exact = [
                phase for phase, run_min, run_max in self.phase_ranges
                if run_min <= run_id <= run_max
            ]
            if exact:
                phases[index] = exact[0]
                continue
            phases[index] = min(
                self.phase_ranges,
                key=lambda item: min(
                    abs(run_id - item[1]), abs(run_id - item[2])
                ),
            )[0]
        return phases.reshape(np.shape(run))

    def absolute_scale_for_phase(self, phase):
        """Return absolute energy-scale factor for commissioning phase(s) 1..4."""
        phases = np.atleast_1d(np.asarray(phase, dtype=np.int64))
        scales = np.empty(len(phases), dtype=np.float64)
        for phase_num, scale in self.absolute_scale_by_phase.items():
            scales[phases == phase_num] = scale
        invalid = ~np.isin(phases, (1, 2, 3, 4))
        if np.any(invalid):
            raise ValueError(f"Invalid phase: {np.unique(phases[invalid])}")
        if np.ndim(phase) == 0:
            return float(scales[0])
        return scales.reshape(np.shape(phase))

    @staticmethod
    def _basis(values, knots, degree):
        values = np.atleast_1d(np.asarray(values, dtype=np.float64))
        n_basis = len(knots) - degree - 1
        basis = np.zeros((len(values), n_basis), dtype=np.float64)
        for index in range(n_basis):
            coefficient = np.zeros(n_basis, dtype=np.float64)
            coefficient[index] = 1.0
            basis[:, index] = BSpline(
                knots, coefficient, degree, extrapolate=True
            )(values)
        return basis

    @classmethod
    def _evaluate_spatial_model(cls, model, r3_m3, costheta):
        r3 = np.clip(
            np.asarray(r3_m3, dtype=np.float64),
            model["r3_min"],
            model["r3_max"],
        )
        ct = np.clip(
            np.asarray(costheta, dtype=np.float64),
            model["costheta_min"],
            model["costheta_max"],
        )
        r3_normalized = (
            (r3 - model["r3_min"])
            / (model["r3_max"] - model["r3_min"])
        )
        x_basis = cls._basis(
            r3_normalized, model["x_knots"], model["degree"]
        )
        y_basis = cls._basis(ct, model["y_knots"], model["degree"])
        design = np.einsum(
            "ij,ik->ijk", x_basis, y_basis
        ).reshape(len(x_basis), -1)
        local_peak = design @ model["coefficient"]
        if np.any(~np.isfinite(local_peak)) or np.any(local_peak <= 0.0):
            raise RuntimeError("Invalid spatial-model local peak")
        return local_peak

    def correct_vertex_rbias(self, x, y, z, position_unit="mm"):
        """Return r-bias-corrected x, y, z in the same unit as input."""
        if position_unit not in {"mm", "m"}:
            raise ValueError("position_unit must be 'mm' or 'm'")
        unit_to_mm = 1000.0 if position_unit == "m" else 1.0
        x_mm, y_mm, z_mm = np.broadcast_arrays(
            np.asarray(x, dtype=np.float64) * unit_to_mm,
            np.asarray(y, dtype=np.float64) * unit_to_mm,
            np.asarray(z, dtype=np.float64) * unit_to_mm,
        )
        radius = np.sqrt(x_mm * x_mm + y_mm * y_mm + z_mm * z_mm)
        bias = np.interp(radius, self.vertex_radius_mm, self.vertex_bias_mm)
        corrected_radius = np.maximum(radius - bias, 0.0)
        scale = np.divide(
            corrected_radius,
            radius,
            out=np.ones_like(radius),
            where=radius > 0.0,
        )
        out_scale = 1.0 / unit_to_mm
        return x_mm * scale * out_scale, y_mm * scale * out_scale, z_mm * scale * out_scale

    def spatial_factor_from_position(self, x, y, z, phase=None, run=None, position_unit="mm"):
        """Evaluate S(r3, costheta) using already r-bias-corrected positions."""
        if position_unit not in {"mm", "m"}:
            raise ValueError("position_unit must be 'mm' or 'm'")
        unit_to_m = 1e-3 if position_unit == "mm" else 1.0
        x_m, y_m, z_m = np.broadcast_arrays(
            np.asarray(x, dtype=np.float64) * unit_to_m,
            np.asarray(y, dtype=np.float64) * unit_to_m,
            np.asarray(z, dtype=np.float64) * unit_to_m,
        )
        radius_m = np.sqrt(x_m * x_m + y_m * y_m + z_m * z_m)
        costheta = np.divide(
            z_m,
            radius_m,
            out=np.zeros_like(radius_m),
            where=radius_m > 0.0,
        )
        if phase is None:
            if run is None:
                raise ValueError("Provide either phase or run")
            phase = self.phase_from_run(run)
        r3 = radius_m ** 3
        r3, costheta, phase = np.broadcast_arrays(
            r3, costheta, np.asarray(phase, dtype=np.int64)
        )
        original_shape = r3.shape
        r3 = r3.ravel()
        costheta = costheta.ravel()
        phase = phase.ravel()
        factor = np.empty(len(r3), dtype=np.float64)
        for phase_num in (1, 2, 3, 4):
            selected = phase == phase_num
            if not np.any(selected):
                continue
            model = self.models[phase_num]
            local_peak = self._evaluate_spatial_model(
                model, r3[selected], costheta[selected]
            )
            factor[selected] = model["target_mev"] / local_peak
        invalid = ~np.isin(phase, (1, 2, 3, 4))
        if np.any(invalid):
            raise ValueError(f"Invalid phase: {np.unique(phase[invalid])}")
        return factor.reshape(original_shape)

    def time_factor(self, event_time):
        """Evaluate T2(t). event_time must be Unix timestamp in UTC seconds."""
        return np.interp(
            np.asarray(event_time, dtype=np.float64),
            self.time_t,
            self.time_scale,
        )

    def correction_factor(self, x, y, z, event_time, phase=None, run=None, position_unit="mm"):
        """Return S(r3,costheta) * absolute_scale(phase) / T2(t) for corrected positions."""
        if phase is None:
            if run is None:
                raise ValueError("Provide either phase or run for absolute energy scale")
            phase = self.phase_from_run(run)
        spatial = self.spatial_factor_from_position(
            x, y, z, phase=phase, run=run, position_unit=position_unit
        )
        time = self.time_factor(event_time)
        if np.any(~np.isfinite(time)) or np.any(time <= 0.0):
            raise RuntimeError("Invalid time correction factor")
        abs_scale = self.absolute_scale_for_phase(phase)
        return spatial * abs_scale / time

    def correct(
        self,
        energy,
        x,
        y,
        z,
        event_time,
        run,
        position_unit="mm",
        apply_vertex=True,
    ):
        """
        Apply the full raw-data correction.

        Returns:
            energy_corr, x_corr, y_corr, z_corr
        """
        if apply_vertex:
            x_corr, y_corr, z_corr = self.correct_vertex_rbias(
                x, y, z, position_unit=position_unit
            )
        else:
            x_corr, y_corr, z_corr = x, y, z
        factor = self.correction_factor(
            x_corr,
            y_corr,
            z_corr,
            event_time,
            run=run,
            position_unit=position_unit,
        )
        energy_corr = np.asarray(energy, dtype=np.float64) * factor
        return energy_corr, x_corr, y_corr, z_corr
