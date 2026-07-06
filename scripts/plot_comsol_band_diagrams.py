#!/usr/bin/env python3
from __future__ import annotations

import csv
import warnings
import re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.ticker import AutoMinorLocator


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/comsol/arch_baseline_pin/Aging"
BASELINE_DIR = ROOT / "data/raw/comsol/arch_baseline_pin/Baseline"
PROCESSED_DIR = ROOT / "data/processed/comsol/architecture_stress_grid"
TABLE_DIR = ROOT / "outputs/tables/comsol_architecture_stress_grid"
FIGURE_DIR = ROOT / "outputs/figures/comsol_architecture_stress_grid"

Q_E = 1.602176634e-19

BAND_CASES = [
    ("stress_light_0_temp_300.csv", "0 sun, 300 K"),
    ("stress_light_0.6_temp_360.csv", "0.60 sun, 360 K"),
    ("stress_light_1_temp_400.csv", "1.00 sun, 400 K"),
]

BAND_COLUMNS = {
    "semi.Ec_e (J)": "Ec",
    "semi.Ev_e (J)": "Ev",
    "semi.Efn_e (J)": "Efn",
    "semi.Efp_e (J)": "Efp",
}

BAND_LABELS = {
    "Ec": r"$E_c$",
    "Ev": r"$E_v$",
    "Efn": r"$E_{Fn}$",
    "Efp": r"$E_{Fp}$",
}

COMSOL_BAND_COLORS = {
    "Ec": "#1F4FFF",
    "Ev": "#00A83B",
    "Efn": "#666666",
    "Efp": "#9A9A9A",
}

COMSOL_BAND_LINESTYLES = {
    "Ec": "-",
    "Ev": "-",
    "Efn": "--",
    "Efp": ":",
}


@dataclass(frozen=True)
class BandCase:
    path: Path
    label: str


def preferred_font() -> str:
    try:
        font_manager.findfont("Arial", fallback_to_default=False)
        return "Arial"
    except ValueError:
        return "DejaVu Sans"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": preferred_font(),
            "font.size": 8,
            "axes.labelsize": 9,
            "axes.labelweight": "bold",
            "axes.titlesize": 9,
            "axes.titleweight": "bold",
            "legend.fontsize": 7,
            "axes.grid": False,
            "axes.linewidth": 1.45,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.major.width": 1.35,
            "ytick.major.width": 1.35,
            "xtick.minor.width": 0.9,
            "ytick.minor.width": 0.9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.dpi": 600,
        }
    )


def style_axes(ax: plt.Axes) -> None:
    ax.tick_params(which="major", length=5, width=1.35, direction="in", top=True, right=True)
    ax.tick_params(which="minor", length=2.5, width=0.9, direction="in", top=True, right=True)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    for spine in ax.spines.values():
        spine.set_linewidth(1.45)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")


def save_figure(fig: plt.Figure, out_base: Path) -> None:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    for suffix in (".png", ".svg", ".pdf"):
        fig.savefig(out_base.with_suffix(suffix), dpi=600, bbox_inches="tight")
    plt.close(fig)


def read_comsol_export(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.startswith("% x,")), None)
    if header_idx is None:
        raise ValueError(f"Could not find COMSOL table header in {path}")
    header = next(csv.reader([lines[header_idx][2:]]))
    data = pd.read_csv(StringIO("\n".join(lines[header_idx + 1 :])), header=None, names=header)
    return data.apply(pd.to_numeric, errors="coerce")


def parse_case_metadata(path: Path) -> tuple[float, int]:
    match = re.fullmatch(r"stress_light_([0-9.]+)_temp_(\d+)\.csv", path.name)
    if not match:
        raise ValueError(f"Unexpected stress-profile filename: {path.name}")
    return float(match.group(1)), int(match.group(2))


def build_long_table(cases: list[BandCase]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for case in cases:
        data = read_comsol_export(case.path)
        light_suns, temperature_k = parse_case_metadata(case.path)
        for column, energy_label in BAND_COLUMNS.items():
            if column not in data.columns:
                raise ValueError(f"{column} is missing from {case.path}")
            part = data[["x", "t", column]].copy()
            part = part.rename(columns={"x": "x_nm", "t": "aging_h", column: "energy_J"})
            part["energy_eV"] = part["energy_J"] / Q_E
            part["energy_level"] = energy_label
            part["source_file"] = case.path.name
            part["case_label"] = case.label
            part["aging_light_suns"] = light_suns
            part["temperature_K"] = temperature_k
            rows.append(part)
    return pd.concat(rows, ignore_index=True)


def build_baseline_equilibrium_table(path: Path) -> pd.DataFrame:
    data = read_comsol_export(path)
    rows: list[pd.DataFrame] = []
    for column, energy_label in BAND_COLUMNS.items():
        if column not in data.columns:
            raise ValueError(f"{column} is missing from {path}")
        part = data[["x", column]].copy()
        part = part.rename(columns={"x": "x_nm", column: "energy_J"})
        part["energy_eV"] = part["energy_J"] / Q_E
        part["energy_level"] = energy_label
        part["source_file"] = path.name
        part["case_label"] = "Dark equilibrium, 300 K"
        rows.append(part)
    return pd.concat(rows, ignore_index=True)


def add_layer_guides(ax: plt.Axes, x_min: float, x_max: float) -> None:
    htl_width_nm = 35.0
    etl_width_nm = 29.0
    htl_right = min(x_min + htl_width_nm, x_max)
    etl_left = max(x_max - etl_width_nm, x_min)

    ax.axvspan(x_min, htl_right, color="#D8E8FF", alpha=0.55, lw=0)
    ax.axvspan(etl_left, x_max, color="#FFE6CC", alpha=0.62, lw=0)
    ax.axvline(htl_right, color="#777777", lw=0.8, ls="--", zorder=1)
    ax.axvline(etl_left, color="#777777", lw=0.8, ls="--", zorder=1)

    label_kwargs = {
        "ha": "center",
        "va": "bottom",
        "fontweight": "bold",
        "fontsize": 7,
        "transform": ax.get_xaxis_transform(),
        "clip_on": False,
        "bbox": {"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.8},
    }
    ax.text((x_min + htl_right) / 2, 1.015, "HTL", **label_kwargs)
    ax.text((htl_right + etl_left) / 2, 1.015, "Perovskite", **label_kwargs)
    ax.text((etl_left + x_max) / 2, 1.015, "ETL", **label_kwargs)


def plot_band_diagram_panel(long_df: pd.DataFrame, aging_h: int = 1000) -> None:
    case_labels = [label for _, label in BAND_CASES]
    subset = long_df.loc[long_df["aging_h"].eq(aging_h)].copy()
    if subset.empty:
        raise ValueError(f"No rows found for aging_h={aging_h}")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.55), sharex=True, sharey=True)
    for ax, case_label in zip(axes, case_labels):
        case_df = subset.loc[subset["case_label"].eq(case_label)]
        if case_df.empty:
            continue
        x_min = float(case_df["x_nm"].min())
        x_max = float(case_df["x_nm"].max())
        for energy_level in ["Ec", "Ev", "Efn", "Efp"]:
            part = case_df.loc[case_df["energy_level"].eq(energy_level)].sort_values("x_nm")
            ax.plot(
                part["x_nm"],
                part["energy_eV"],
                color=COMSOL_BAND_COLORS[energy_level],
                ls=COMSOL_BAND_LINESTYLES[energy_level],
                lw=1.75,
                label=BAND_LABELS[energy_level],
                zorder=3,
            )
        ax.set_xlim(x_min, x_max)
        ax.set_xlabel("Position (nm)")
        ax.text(
            0.04,
            0.08,
            case_label,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontweight="bold",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 1.5},
        )
        style_axes(ax)

    y0, y1 = axes[0].get_ylim()
    pad = 0.08 * (y1 - y0)
    for ax in axes:
        ax.set_ylim(y0 - pad, y1 + pad)
        add_layer_guides(ax, float(subset["x_nm"].min()), float(subset["x_nm"].max()))
    axes[0].set_ylabel("Energy (eV)")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, -0.03),
    )
    save_figure(fig, FIGURE_DIR / "baseline_pin_band_diagrams_selected_cases")


def plot_zero_light_300k_reference(long_df: pd.DataFrame) -> None:
    case_label = "0 sun, 300 K"
    times = [0, 1000]
    case_df = long_df.loc[long_df["case_label"].eq(case_label)].copy()
    if case_df.empty:
        raise ValueError(f"No rows found for {case_label}")

    fig, axes = plt.subplots(2, 1, figsize=(4.2, 5.1), sharex=True, sharey=True)
    for ax, aging_h in zip(axes, times):
        subset = case_df.loc[case_df["aging_h"].eq(aging_h)]
        if subset.empty:
            raise ValueError(f"No rows found for {case_label} at {aging_h} h")
        for energy_level in ["Ec", "Efn", "Efp", "Ev"]:
            part = subset.loc[subset["energy_level"].eq(energy_level)].sort_values("x_nm")
            ax.plot(
                part["x_nm"],
                part["energy_eV"],
                color=COMSOL_BAND_COLORS[energy_level],
                ls=COMSOL_BAND_LINESTYLES[energy_level],
                lw=1.65 if energy_level in {"Ec", "Ev"} else 1.25,
                label=BAND_LABELS[energy_level],
                zorder=3,
            )
        ax.set_xlim(float(case_df["x_nm"].min()), float(case_df["x_nm"].max()))
        ax.text(
            0.035,
            0.07,
            f"{case_label}, {aging_h:g} h",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontweight="bold",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.80, "pad": 1.5},
        )
        style_axes(ax)

    y0, y1 = axes[0].get_ylim()
    pad = 0.07 * (y1 - y0)
    for ax in axes:
        ax.set_ylim(y0 - pad, y1 + pad)
        add_layer_guides(ax, float(case_df["x_nm"].min()), float(case_df["x_nm"].max()))
        ax.set_ylabel("Energy (eV)")
    axes[-1].set_xlabel("Position (nm)")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles, labels, loc="upper right", frameon=True, fancybox=False, edgecolor="#888888")
    save_figure(fig, FIGURE_DIR / "baseline_pin_band_diagram_0sun_300K_comsol_style")


def plot_baseline_equilibrium_band_diagram(equilibrium_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(1, 1, figsize=(4.7, 3.25))
    for energy_level in ["Ec", "Efn", "Efp", "Ev"]:
        part = equilibrium_df.loc[equilibrium_df["energy_level"].eq(energy_level)].sort_values("x_nm")
        ax.plot(
            part["x_nm"],
            part["energy_eV"],
            color=COMSOL_BAND_COLORS[energy_level],
            ls=COMSOL_BAND_LINESTYLES[energy_level],
            lw=1.75 if energy_level in {"Ec", "Ev"} else 1.25,
            label=BAND_LABELS[energy_level],
            zorder=3,
        )
    x_min = float(equilibrium_df["x_nm"].min())
    x_max = float(equilibrium_df["x_nm"].max())
    ax.set_xlim(x_min, x_max)
    ax.set_xlabel("Position (nm)")
    ax.set_ylabel("Energy (eV)")
    ax.text(
        0.035,
        0.07,
        "Dark equilibrium, 300 K",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontweight="bold",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.80, "pad": 1.5},
    )
    style_axes(ax)
    y0, y1 = ax.get_ylim()
    pad = 0.07 * (y1 - y0)
    ax.set_ylim(y0 - pad, y1 + pad)
    add_layer_guides(ax, x_min, x_max)
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        frameon=True,
        fancybox=False,
        edgecolor="#888888",
        borderaxespad=0.3,
    )
    save_figure(fig, FIGURE_DIR / "baseline_pin_band_diagram_dark_equilibrium_300K")


def plot_band_evolution(long_df: pd.DataFrame, case_label: str = "1.00 sun, 400 K") -> None:
    times = [0, 1000]
    fig, axes = plt.subplots(1, 2, figsize=(5.4, 2.55), sharex=True, sharey=True)
    case_df = long_df.loc[long_df["case_label"].eq(case_label)]
    for ax, aging_h in zip(axes, times):
        subset = case_df.loc[case_df["aging_h"].eq(aging_h)]
        for energy_level in ["Ec", "Ev", "Efn", "Efp"]:
            part = subset.loc[subset["energy_level"].eq(energy_level)].sort_values("x_nm")
            ax.plot(
                part["x_nm"],
                part["energy_eV"],
                color=COMSOL_BAND_COLORS[energy_level],
                ls=COMSOL_BAND_LINESTYLES[energy_level],
                lw=1.75,
                label=BAND_LABELS[energy_level],
                zorder=3,
            )
        ax.set_xlabel("Position (nm)")
        ax.text(
            0.04,
            0.08,
            f"{aging_h:g} h",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontweight="bold",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 1.5},
        )
        style_axes(ax)

    y0, y1 = axes[0].get_ylim()
    pad = 0.08 * (y1 - y0)
    for ax in axes:
        ax.set_ylim(y0 - pad, y1 + pad)
        add_layer_guides(ax, float(case_df["x_nm"].min()), float(case_df["x_nm"].max()))
    axes[0].set_ylabel("Energy (eV)")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.03))
    save_figure(fig, FIGURE_DIR / "baseline_pin_band_diagram_evolution_1sun_400K")


def main() -> None:
    configure_style()
    baseline_path = BASELINE_DIR / "Energy Diagram.csv"
    cases = [BandCase(RAW_DIR / file_name, label) for file_name, label in BAND_CASES]
    missing = [case.path for case in cases if not case.path.exists()]
    if not baseline_path.exists():
        missing.append(baseline_path)
    if missing:
        raise FileNotFoundError(f"Missing band-profile exports: {missing}")
    equilibrium_df = build_baseline_equilibrium_table(baseline_path)
    long_df = build_long_table(cases)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    out_processed = PROCESSED_DIR / "baseline_pin_band_profiles_long.csv"
    out_table = TABLE_DIR / "baseline_pin_band_profiles_long.csv"
    out_equilibrium = TABLE_DIR / "baseline_pin_band_dark_equilibrium_300K.csv"
    equilibrium_df.to_csv(out_equilibrium, index=False)
    long_df.to_csv(out_processed, index=False)
    try:
        long_df.to_csv(out_table, index=False)
    except OSError as exc:
        warnings.warn(f"Could not update generated table copy {out_table}: {exc}", RuntimeWarning)
    plot_baseline_equilibrium_band_diagram(equilibrium_df)
    plot_band_diagram_panel(long_df, aging_h=1000)
    plot_zero_light_300k_reference(long_df)
    plot_band_evolution(long_df)
    print(f"Wrote {out_equilibrium}")
    print(f"Wrote {out_processed}")
    print(f"Wrote {out_table}")
    print(f"Wrote figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
