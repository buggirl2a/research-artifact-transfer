from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(r"C:\range_paper")
PKG = ROOT / "10_archive" / "d10e" / "pkg"
OUT = PKG / "out"
FIG = PKG / "fig"


def finish(fig: plt.Figure, name: str) -> None:
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for path in FIG.glob("*.png"):
        path.unlink()
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 120,
    })

    state = pd.read_csv(OUT / "state_summary_v01.csv", encoding="utf-8-sig")
    states = [f"E{i}" for i in range(6)]
    s = state[(state.observation_regime == "O1") & (state.orientation == "ALL")].set_index("state").loc[states]
    values = s.separation_pp.to_numpy(float)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    colors = ["#2B6F9C" if value >= 0 else "#C55A3D" for value in values]
    bars = ax.bar(states, values, color=colors, width=0.68)
    ax.axhline(0, color="#4B5563", lw=0.8)
    ax.set_ylabel("STRONG − PAIRED_NULL separation (pp)")
    ax.set_title("D10E measurement states")
    ax.grid(axis="y", color="#D9E2EA", lw=0.6)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + (0.8 if value >= 0 else -0.8), f"{value:.2f}", ha="center", va="bottom" if value >= 0 else "top")
    finish(fig, "state_separation_v01.png")

    decomp = pd.read_csv(OUT / "source_decomp_v01.csv", encoding="utf-8-sig")
    d = decomp[(decomp.observation_regime == "O1") & (decomp.orientation == "ALL") & (decomp.metric == "separation_pp")]
    labels = ["Expected operator\nE3−E0", "Normalization\nE4−E3", "Finite realization\nE5−E4", "Current draw\nE1−E5"]
    vals = d.set_index("component").loc[[
        "A_SYSTEMATIC_MEASUREMENT_OPERATOR",
        "B_NORMALIZATION_NONLINEARITY",
        "C_FINITE_REALIZATION_DOWNSTREAM",
        "D_CURRENT_REALIZATION_DEVIATION",
    ], "component_value_pp"].to_numpy(float)
    fig, ax = plt.subplots(figsize=(7.2, 4.1))
    bars = ax.bar(labels, vals, color=["#2B6F9C", "#77A6C7", "#C55A3D", "#E3A27D"], width=0.65)
    ax.axhline(0, color="#4B5563", lw=0.8)
    ax.set_ylabel("Contribution to separation (pp)")
    ax.set_title("Source decomposition")
    ax.grid(axis="y", color="#D9E2EA", lw=0.6)
    for bar, value in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, value + (0.7 if value >= 0 else -0.7), f"{value:.2f}", ha="center", va="bottom" if value >= 0 else "top")
    finish(fig, "source_decomposition_v01.png")

    ladder = pd.read_csv(OUT / "k_ladder_summary_v01.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(7.2, 4.1))
    for orientation, color, marker in (("AB", "#2B6F9C", "o"), ("BA", "#C55A3D", "s")):
        sub = ladder[(ladder.orientation == orientation) & (ladder.metric == "separation_pp")].sort_values("K")
        ax.plot(sub.K, sub["mean"], marker=marker, color=color, lw=1.8, label=orientation)
        ax.fill_between(sub.K, sub.q05, sub.q95, color=color, alpha=0.13)
    e0 = float(s.loc["E0", "separation_pp"])
    ax.axhline(e0, color="#3F7D4A", ls="--", lw=1.2, label=f"E0 reference ({e0:.2f} pp)")
    ax.axhline(0, color="#4B5563", lw=0.7)
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 2, 4, 8, 16, 32], ["1", "2", "4", "8", "16", "32"])
    ax.set_xlabel("Independent observation realizations averaged (K)")
    ax.set_ylabel("Separation (pp)")
    ax.set_title("Repeated-survey averaging ladder")
    ax.grid(axis="y", color="#D9E2EA", lw=0.6)
    ax.legend(frameon=False, ncol=3, loc="lower right")
    finish(fig, "k_ladder_v01.png")

    unc = pd.read_csv(OUT / "uncertainty_summary_v01.csv", encoding="utf-8-sig")
    unc["group"] = unc.world.str.replace("PAIRED_NULL", "NULL", regex=False) + " " + unc.orientation
    x = np.arange(len(unc))
    width = 0.24
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.bar(x - width, unc.empirical_variance_normal_interval_coverage_mean, width, label="Empirical-variance interval", color="#2B6F9C")
    ax.bar(x, unc.poisson_plugin_interval_coverage_mean, width, label="Poisson plug-in interval", color="#C55A3D")
    ax.bar(x + width, unc.current_E1_poisson_interval_coverage, width, label="Current E1 Poisson interval", color="#E3A27D")
    ax.axhline(0.95, color="#3F7D4A", ls="--", lw=1.0, label="0.95 reference")
    ax.set_xticks(x, unc.group)
    ax.set_ylim(0.55, 1.01)
    ax.set_ylabel("Coverage")
    ax.set_title("Empirical and Poisson-style interval coverage")
    ax.grid(axis="y", color="#D9E2EA", lw=0.6)
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    finish(fig, "uncertainty_coverage_v01.png")


if __name__ == "__main__":
    main()
