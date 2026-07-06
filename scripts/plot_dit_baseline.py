#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import AutoMinorLocator


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "comsol" / "arch_baseline_pin" / "Baseline" / "DIT.csv"
OUT_DIR = ROOT / "outputs" / "figures" / "dit"
TABLE_DIR = ROOT / "outputs" / "tables" / "dit"


def _style_axes(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_linewidth(1.6)
        spine.set_color("black")
    ax.tick_params(which="major", direction="in", top=True, right=True, length=5.5, width=1.35)
    ax.tick_params(which="minor", direction="in", top=True, right=True, length=2.8, width=1.0)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    if ax.get_yscale() == "linear":
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")


def _save_multi_format(fig: plt.Figure, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(out_path.with_suffix(f".{suffix}"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def load_comsol_global_eval(path: Path) -> pd.DataFrame:
    header: list[str] | None = None
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("%"):
            candidate = stripped.lstrip("%").strip()
            if "Time (s)" in candidate and "," in candidate:
                header = [part.strip() for part in candidate.split(",")]
            continue
        rows.append([part.strip() for part in stripped.split(",")])
    if header is None:
        raise ValueError(f"No COMSOL commented header found in {path}")
    data = pd.DataFrame(rows, columns=header)
    for col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="raise")
    data = data.rename(
        columns={
            "Time (s)": "time_s",
            "Average terminal current density (mA/cm^2)": "current_density_mAcm2",
        }
    )
    data["time_ms"] = data["time_s"] * 1000.0
    return data


def summarize_baseline(data: pd.DataFrame) -> pd.DataFrame:
    current = data["current_density_mAcm2"].to_numpy(dtype=float)
    time_s = data["time_s"].to_numpy(dtype=float)
    abs_current = np.abs(current)
    spike_idx = int(np.nanargmax(abs_current))
    tail = current[-max(10, min(80, current.size // 5)) :]
    baseline = float(np.nanmedian(tail))
    corrected = current - baseline
    charge_density_mc_cm2 = float(np.trapezoid(corrected * 1e-3, time_s) * 1e3)
    return pd.DataFrame(
        [
            {
                "source_file": str(INPUT.relative_to(ROOT)).replace("\\", "/"),
                "n_points": int(data.shape[0]),
                "light_on": int(data["light_on"].iloc[0]),
                "use_scan": int(data["use_scan"].iloc[0]),
                "time_min_ms": float(data["time_ms"].min()),
                "time_max_ms": float(data["time_ms"].max()),
                "tail_baseline_mAcm2": baseline,
                "peak_abs_current_mAcm2": float(abs_current[spike_idx]),
                "peak_time_ms": float(data["time_ms"].iloc[spike_idx]),
                "integrated_baseline_corrected_mCcm2": charge_density_mc_cm2,
            }
        ]
    )


def plot_baseline(data: pd.DataFrame, summary: pd.DataFrame, out_path: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 8,
            "axes.labelsize": 10,
            "axes.labelweight": "bold",
            "legend.fontsize": 8,
            "axes.grid": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )

    t_ms = data["time_ms"].to_numpy(dtype=float)
    j = data["current_density_mAcm2"].to_numpy(dtype=float)
    baseline = float(summary["tail_baseline_mAcm2"].iloc[0])
    j_corr = j - baseline
    abs_corr = np.abs(j_corr)
    scale = float(np.nanmax(abs_corr)) or 1.0

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 2.75))
    color = "#F0444A"

    axes[0].plot(t_ms, j, color=color, lw=1.8)
    axes[0].axhline(baseline, color="black", lw=0.9, ls=":")
    axes[0].set_xlabel("Time (ms)")
    axes[0].set_ylabel("Current density (mA cm$^{-2}$)")

    axes[1].plot(t_ms, j_corr, color=color, lw=1.8)
    axes[1].axhline(0, color="black", lw=0.9, ls=":")
    axes[1].set_xlabel("Time (ms)")
    axes[1].set_ylabel("Baseline-corrected $J$ (mA cm$^{-2}$)")

    axes[2].semilogy(t_ms, np.maximum(abs_corr / scale, 1e-12), color=color, lw=1.8)
    axes[2].set_xlabel("Time (ms)")
    axes[2].set_ylabel("Normalized magnitude")
    axes[2].set_ylim(1e-9, 2)

    annotation = (
        f"light_on = {int(summary['light_on'].iloc[0])}\n"
        f"use_scan = {int(summary['use_scan'].iloc[0])}\n"
        f"peak = {summary['peak_abs_current_mAcm2'].iloc[0]:.2g} mA cm$^{{-2}}$\n"
        f"tail = {baseline:.2g} mA cm$^{{-2}}$"
    )
    axes[2].text(
        0.97,
        0.95,
        annotation,
        transform=axes[2].transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="0.25", linewidth=0.8),
    )

    for label, ax in zip(("a)", "b)", "c)"), axes):
        _style_axes(ax)
        ax.text(0.02, 0.96, label, transform=ax.transAxes, ha="left", va="top", fontsize=11, fontweight="bold")

    _save_multi_format(fig, out_path)


def main() -> None:
    data = load_comsol_global_eval(INPUT)
    summary = summarize_baseline(data)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data.to_csv(TABLE_DIR / "dit_baseline_control_long.csv", index=False)
    summary.to_csv(TABLE_DIR / "dit_baseline_control_summary.csv", index=False)
    plot_baseline(data, summary, OUT_DIR / "dit_baseline_control.png")
    print(f"Wrote {OUT_DIR / 'dit_baseline_control.png'}")
    print(f"Wrote {TABLE_DIR / 'dit_baseline_control_summary.csv'}")


if __name__ == "__main__":
    main()
