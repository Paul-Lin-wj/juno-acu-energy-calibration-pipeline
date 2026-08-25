"""
cuts_parser.py — extract & archive the selection (cut) conditions of a run.

Two layers of cut provenance are preserved per run:

  1. STATIC cut logic  — the constants hard-coded in src/combine_selection.py
     (nominal source energies, ROI scan scales, fit window, EFV ellipse form).
     These are archived verbatim via code_snapshot/sha256 (see run_logger).

  2. RUNTIME cut values — the numbers the robust scan decided for THIS run,
     parsed from the combine_selection console output:
       ROI, Step-1 energy region, Z-cut (z_limit / RD threshold / robust
       crossing), z_expected, EFV acceptance, final energy cut window,
       MuonVeto keep fractions, event counts.

Output: cuts/<RUN>_cuts.json + a markdown row appended to cuts/summary.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# --- static cut constants, kept in sync with src/combine_selection.py ---
# (verified 2026-08-24 against the audited file; sha256 in code_snapshot is
#  the authoritative record — this table is for human readability)
STATIC_CUTS = {
    "nominal_energy_MeV": {
        "Cs137": 0.662, "Mn54": 0.835, "Ge68": 1.022, "K40": 1.461,
        "nH": 2.223, "Co60": 2.506, "nC": 4.94, "O16": 6.13, "AmC": 2.223,
    },
    "fit_window_scale": {"low": 0.9, "high": 1.1},   # around Step-1 region
    "fit_bin_width_MeV": 0.002,
    "source_initial_ROI_scale_MeV": {"Ge68": [0.45, 1.20]},
    "EFV_ellipse": "sqrt((rho/rho_limit)^2 + ((z - z_expected)/z_limit)^2) <= 1",
    "EFV_z_exclusion": "|z| >= 17.7 m dropped before EFV",
    "muon_veto": "keep events with MuonVeto == False",
    "energy_cut_definition": "mu +/- 3 sigma of fitted peak (Gaussian on Step-1 region)",
}


def parse_selection_console(text: str, run: int) -> dict:
    """Parse the runtime cut values from one combine_selection console log."""
    cuts: dict = {"run": run}

    def grab(pattern, cast=str, name=None):
        m = re.search(pattern, text)
        if m:
            cuts[name or pattern] = cast(m.group(1))
        return m

    # Source / bkg configuration
    m = re.search(r"Configuration: Source=(\S+), BkgRun=(\d+)", text)
    if m:
        cuts["source"], cuts["bkg_run"] = m.group(1), int(m.group(2))

    # ROI & robust energy region
    m = re.search(r"ROI: \[([\d.]+), ([\d.]+)\] MeV", text)
    if m:
        cuts["ROI_MeV"] = [float(m.group(1)), float(m.group(2))]
    m = re.search(r"Step1 Energy Region \(robust\): \[([\d.]+), ([\d.]+)\] MeV", text)
    if m:
        cuts["step1_energy_region_MeV"] = [float(m.group(1)), float(m.group(2))]

    # Z-cut robust scan
    m = re.search(r"Step3 Z-cut: RD_threshold=([\d.]+)%, z_limit=([\d.]+) m", text)
    if m:
        cuts["z_cut"] = {"RD_threshold_percent": float(m.group(1)),
                         "z_limit_m": float(m.group(2))}
    m = re.search(r"z_expected: ([\d.]+) m; True: ([\d.]+) m", text)
    if m:
        cuts["z_expected_m"] = float(m.group(1))
        cuts["z_source_true_m"] = float(m.group(2))

    # MuonVeto keep fractions
    for tag, key in ((f"Calib RUN{run}", "calib"), ("Bkg", "bkg")):
        m = re.search(re.escape(tag) + r".*?: (\d+)/(\d+) events kept \(([\d.]+)%\)", text)
        if m:
            cuts[f"{key}_muonveto_kept"] = {
                "kept": int(m.group(1)), "total": int(m.group(2)),
                "percent": float(m.group(3))}

    # EFV acceptance
    m = re.search(rf"RUN{run}: EFV event number: (\d+)/(\d+)", text)
    if m:
        cuts["EFV_selected"] = {"kept": int(m.group(1)), "input": int(m.group(2))}

    # Final energy cut
    m = re.search(r"Final Energy Cut \(mu±3sigma\): \[([\d.]+), ([\d.]+)\] MeV", text)
    if m:
        cuts["final_energy_cut_MeV"] = [float(m.group(1)), float(m.group(2))]
    m = re.search(r"Events after Ecut: (\d+)", text)
    if m:
        cuts["events_after_ecut"] = int(m.group(1))

    return cuts


def write_cuts_record(out_dir: Path, run: int, console_text: str) -> dict:
    """Write cuts/<RUN>_cuts.json and append to cuts/summary.md."""
    cuts = parse_selection_console(console_text, run)
    cuts["static_cut_definitions"] = STATIC_CUTS
    cuts_dir = Path(out_dir) / "cuts"
    cuts_dir.mkdir(parents=True, exist_ok=True)
    with open(cuts_dir / f"{run}_cuts.json", "w") as f:
        json.dump(cuts, f, indent=1, ensure_ascii=False)

    md = cuts_dir / "summary.md"
    row = (f"| {run} | {cuts.get('source','?')} | "
           f"{cuts.get('ROI_MeV','—')} | {cuts.get('step1_energy_region_MeV','—')} | "
           f"{cuts.get('z_cut',{}).get('z_limit_m','—')} | "
           f"{cuts.get('final_energy_cut_MeV','—')} | "
           f"{cuts.get('EFV_selected',{}).get('kept','—')} | "
           f"{cuts.get('events_after_ecut','—')} |\n")
    if not md.exists():
        md.write_text(
            "# Selection cut conditions (runtime, robust-scan decisions)\n\n"
            "| run | source | ROI [MeV] | Step-1 region [MeV] | z_limit [m] | "
            "E-cut [MeV] | EFV kept | after Ecut |\n"
            "|---|---|---|---|---|---|---|---|\n")
    with open(md, "a") as f:
        f.write(row)
    return cuts
