# -----------------------------------------------------------------------------
# NhnCFitter.py — 逐字节移植自 Shubing Liu 的 nH_nC_fitter.py（2026-05-20 版）：
#   ENL_agent/juno_calibration_acu_gamma_source/AmC_nH-nC_fitter/
#   npz_fromFinalcorrection/nH_nC_fitter.py
# 摘取：GaussianFitter 类 + FIT_CONFIG + MIN_EVENTS（拟合窗口/初值/最小事例数
# 全部原值，未改任何数字）。入口编排移至 pipeline/run_amc_fit_all.py。
# 溯源与 md5 对照见 amcsel/PROVENANCE.md。
# -----------------------------------------------------------------------------
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from iminuit import Minuit

# ---------------------------------------------------------------------------
# Fit configuration（原值）
# ---------------------------------------------------------------------------
FIT_CONFIG = {
    "nH": {
        "fit_range":  (2.05, 2.35),
        "plot_range": (2.00, 2.40),
        "init_mu":    2.20,
        "init_sigma": 0.06,
        "title":      "nH (2.22 MeV) --- RUN{run_id}",
    },
    "nC": {
        "fit_range":  (4.70, 5.30),
        "plot_range": (4.60, 5.40),
        "init_mu":    4.94,
        "init_sigma": 0.10,
        "title":      "nC (4.95 MeV) --- RUN{run_id}",
    },
}

MIN_EVENTS = {"nH": 50, "nC": 20}


class GaussianFitter:
    """
    Histogram data over the plot_range, fit bins within the fit_range
    using binned Poisson likelihood (iminuit).
    """

    def __init__(self, energy_array, plot_range, fit_range, init_mu, init_sigma, bins=100):
        self.energy_array = energy_array
        self.plot_min, self.plot_max = plot_range
        self.fit_min,  self.fit_max  = fit_range
        self.bins = bins

        counts, edges = np.histogram(
            energy_array, bins=bins, range=(self.plot_min, self.plot_max)
        )
        self.hist        = counts
        self.bin_edges   = edges
        self.bin_centers = (edges[:-1] + edges[1:]) / 2
        self.bin_width   = float(edges[1] - edges[0]) if len(edges) > 1 else 1.0

        self.fit_mask = (
            (self.bin_centers >= self.fit_min) & (self.bin_centers <= self.fit_max)
        )
        self.hist_err = np.sqrt(np.maximum(counts, 1))
        self.m = None
        self.result = None
        self._build_minuit(init_mu, init_sigma)

    @staticmethod
    def _expected_counts(x, N, mu, sigma, bin_width):
        sigma = max(float(sigma), 1e-12)
        return N * bin_width / (sigma * np.sqrt(2 * np.pi)) * np.exp(
            -0.5 * ((x - mu) / sigma) ** 2
        )

    @staticmethod
    def _gauss_peak_amp(N, sigma):
        sigma = max(float(sigma), 1e-12)
        return N / (sigma * np.sqrt(2 * np.pi))

    @staticmethod
    def _gauss(x, amp, mu, sigma):
        return amp * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    def _build_minuit(self, init_mu, init_sigma):
        x = self.bin_centers[self.fit_mask]
        y = self.hist[self.fit_mask]
        bw = self.bin_width

        init_N = float(np.sum(y)) if len(y) > 0 else 1.0
        if init_N < 1:
            init_N = 1.0

        def cost(N, mu, sigma):
            mu_bins = np.maximum(self._expected_counts(x, N, mu, sigma, bw), 1e-12)
            return float(2.0 * np.sum(mu_bins - y * np.log(mu_bins)))

        self.m = Minuit(cost, N=init_N, mu=init_mu, sigma=init_sigma)
        self.m.limits["N"]     = (0.0, None)
        self.m.limits["sigma"] = (0.005, None)
        self.m.strategy = 2
        self.m.errordef = Minuit.LIKELIHOOD
        self.m.limits["mu"] = (self.fit_min, self.fit_max)


    def fit(self):
        self.m.migrad()
        self.m.hesse()

        x = self.bin_centers[self.fit_mask]
        y = self.hist[self.fit_mask]
        bw = self.bin_width
        N = float(self.m.values["N"])
        mu = float(self.m.values["mu"])
        sigma = float(self.m.values["sigma"])
        mu_bins = self._expected_counts(x, N, mu, sigma, bw)
        chi2 = float(np.sum((y - mu_bins) ** 2 / np.maximum(mu_bins, 1e-12)))
        ndf = int(self.fit_mask.sum() - len(self.m.values))

        self.result = {
            "mu":        mu,
            "mu_err":    float(self.m.errors["mu"]),
            "sigma":     sigma,
            "sigma_err": float(self.m.errors["sigma"]),
            "amp":       float(self._gauss_peak_amp(N, sigma)),
            "chi2":      chi2,
            "nll":       float(self.m.fval),
            "ndf":       ndf,
            "entry":     int(len(self.energy_array)),
            "fit_valid": int(self.m.valid),
        }
        return self.m.valid


    def make_axes(self, ax, run_id, title_template):
        """Draw data, fit curve, fit-range markers, and stats box onto ax."""
        r = self.result
        mu, sigma = r["mu"], r["sigma"]
        N = float(self.m.values["N"])

        ax.errorbar(
            self.bin_centers, self.hist, yerr=self.hist_err,
            fmt="o", color="black", markersize=4, linewidth=1,
            capsize=2, label="Data",
        )

        x_fine = np.linspace(self.fit_min, self.fit_max, 600)
        y_fine = self._expected_counts(x_fine, N, mu, sigma, self.bin_width)
        ax.plot(
            x_fine, y_fine,
            "r-", linewidth=2, label="Gaussian fit",
        )

        label_fit_range = "Fit range [{:.2f}, {:.2f}] MeV".format(self.fit_min, self.fit_max)
        ax.axvline(self.fit_min, color="gray", linestyle="--", linewidth=1.2,
                   label=label_fit_range)
        ax.axvline(self.fit_max, color="gray", linestyle="--", linewidth=1.2)

        ax.set_xlim(self.plot_min, self.plot_max)
        ax.set_title(title_template.format(run_id=run_id), fontsize=13, fontweight="bold")
        ax.set_xlabel("Energy (MeV)", fontsize=12)
        ax.set_ylabel("Counts", fontsize=12)
        ax.tick_params(direction="in", which="both", top=True, right=True)
        ax.legend(fontsize=10)

        res = sigma / mu if mu != 0 else 0.0
        stats = (
            "Entries: {}".format(r["entry"])
            + "\n"
            + r"$\mu$: {:.4f} $\pm$ {:.4f} MeV".format(mu, r["mu_err"])
            + "\n"
            + r"$\sigma$: {:.4f} $\pm$ {:.4f} MeV".format(sigma, r["sigma_err"])
            + "\n"
            + r"$\sigma/\mu$: {:.2f} %".format(100 * res)
            + "\n"
            + r"$\chi^2$/ndf: {:.1f} / {}".format(r["chi2"], r["ndf"])
        )
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.85)
        ax.text(
            0.03, 0.97, stats,
            transform=ax.transAxes, fontsize=10,
            verticalalignment="top", bbox=props, family="monospace",
        )
