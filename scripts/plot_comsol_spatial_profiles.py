#!/usr/bin/env python3
from __future__ import annotations

import csv
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
RAW_DIR = ROOT / "data/raw/comsol/arch_baseline_pin/Aging/profile_grid_light_temperature"
TABLE_DIR = ROOT / "outputs/tables/comsol_architecture_stress_grid"
FIGURE_DIR = ROOT / "outputs/figures/comsol_architecture_stress_grid"

TIME_INDEX_TO_H = {
    1: 0,
    2: 50,
    3: 100,
    4: 200,
    5: 300,
    6: 400,
    7: 500,
    8: 600,
    9: 800,
    10: 1000,
}

PVK_LEFT_NM = 64.0
PVK_RIGHT_NM = 460.0


@dataclass(frozen=True)
class ProfileCase:
    file_name: str
    label: str


CASES = [
    ProfileCase("profile_grid_temp_300K_light_0p01sun.csv", "0 sun, 300 K"),
    ProfileCase("profile_grid_temp_360K_light_0p60sun.csv", "0.60 sun, 360 K"),
    ProfileCase("profile_grid_temp_400K_light_1p00sun.csv", "1.00 sun, 400 K"),
]


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


def add_layer_guides(ax: plt.Axes) -> None:
    y0, y1 = ax.get_ylim()
    ax.axvspan(29, PVK_LEFT_NM, color="#D8E8FF", alpha=0.45, lw=0, zorder=0)
    ax.axvspan(PVK_RIGHT_NM, 489, color="#FFE6CC", alpha=0.55, lw=0, zorder=0)
    ax.axvline(PVK_LEFT_NM, color="#777777", lw=0.8, ls="--", zorder=1)
    ax.axvline(PVK_RIGHT_NM, color="#777777", lw=0.8, ls="--", zorder=1)
    ax.set_ylim(y0, y1)


def read_profile(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.startswith("% x,")), None)
    if header_idx is None:
        raise ValueError(f"Could not find profile header in {path}")
    header = next(csv.reader([lines[header_idx][2:]]))
    data = pd.read_csv(StringIO("\n".join(lines[header_idx + 1 :])), header=None, names=header)
    return data.apply(pd.to_numeric, errors="coerce")


def column_for(data: pd.DataFrame, variable_prefix: str, aging_h: int) -> str:
    time_index = next(k for k, v in TIME_INDEX_TO_H.items() if v == aging_h)
    matches = [
        col
        for col in data.columns
        if col.startswith(variable_prefix) and f"@ {time_index}:" in col
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one column for {variable_prefix} at {aging_h} h, found {matches}")
    return matches[0]


def load_cases() -> dict[str, pd.DataFrame]:
    loaded: dict[str, pd.DataFrame] = {}
    for case in CASES:
        path = RAW_DIR / case.file_name
        if not path.exists():
            raise FileNotFoundError(path)
        loaded[case.label] = read_profile(path)
    return loaded


def plot_final_profiles(data_by_case: dict[str, pd.DataFrame]) -> None:
    variables = [
        ("uion", r"$u_{\mathrm{ion}}$", "uion", 1.0),
        ("Dtrap", r"$D_{\mathrm{trap}}$", "Dtrap", 1.0),
        ("semi.Rsrh", r"$R_{\mathrm{SRH}}$ ($10^{27}$ m$^{-3}$ s$^{-1}$)", "Rsrh", 1e-27),
        ("semi.EX", r"$E_x$ (MV m$^{-1}$)", "Ex", 1e-6),
    ]
    colors = {
        "0 sun, 300 K": "#555555",
        "0.60 sun, 360 K": "#F57C00",
        "1.00 sun, 400 K": "#1F77E5",
    }
    fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.15), sharex=True)
    for ax, (prefix, ylabel, _, scale) in zip(axes.flat, variables):
        for label, data in data_by_case.items():
            x = data["x"].to_numpy(dtype=float)
            y = data[column_for(data, prefix, 1000)].to_numpy(dtype=float) * scale
            ax.plot(x, y, lw=1.75, color=colors[label], label=label)
        ax.set_xlim(29, 489)
        ax.set_ylabel(ylabel)
        add_layer_guides(ax)
        style_axes(ax)
    axes[1, 0].set_xlabel("Position (nm)")
    axes[1, 1].set_xlabel("Position (nm)")
    axes[0, 0].legend(loc="best", frameon=False)
    save_figure(fig, FIGURE_DIR / "baseline_pin_spatial_profiles_selected_cases")


def plot_high_stress_evolution(data: pd.DataFrame) -> None:
    variables = [
        ("uion", r"$u_{\mathrm{ion}}$", 1.0),
        ("Dtrap", r"$D_{\mathrm{trap}}$", 1.0),
        ("semi.Rsrh", r"$R_{\mathrm{SRH}}$ ($10^{27}$ m$^{-3}$ s$^{-1}$)", 1e-27),
        ("semi.EX", r"$E_x$ (MV m$^{-1}$)", 1e-6),
    ]
    times = [0, 200, 600, 1000]
    colors = {
        0: "#555555",
        200: "#F57C00",
        600: "#159A2F",
        1000: "#1F77E5",
    }
    fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.15), sharex=True)
    for ax, (prefix, ylabel, scale) in zip(axes.flat, variables):
        for aging_h in times:
            x = data["x"].to_numpy(dtype=float)
            y = data[column_for(data, prefix, aging_h)].to_numpy(dtype=float) * scale
            ax.plot(x, y, lw=1.75, color=colors[aging_h], label=f"{aging_h:g} h")
        ax.set_xlim(29, 489)
        ax.set_ylabel(ylabel)
        add_layer_guides(ax)
        style_axes(ax)
    axes[1, 0].set_xlabel("Position (nm)")
    axes[1, 1].set_xlabel("Position (nm)")
    axes[0, 0].legend(loc="best", frameon=False)
    save_figure(fig, FIGURE_DIR / "baseline_pin_spatial_profiles_high_stress_time_evolution")


def write_conservation_summary(data_by_case: dict[str, pd.DataFrame]) -> None:
    rows = []
    for label, data in data_by_case.items():
        x = data["x"].to_numpy(dtype=float)
        pvk = (x >= PVK_LEFT_NM) & (x <= PVK_RIGHT_NM)
        for aging_h in [0, 50, 100, 200, 300, 400, 500, 600, 800, 1000]:
            u = data[column_for(data, "uion", aging_h)].to_numpy(dtype=float)
            dtrap = data[column_for(data, "Dtrap", aging_h)].to_numpy(dtype=float)
            nt_cm3 = data[column_for(data, "Nt_eff_lat_bulk", aging_h)].to_numpy(dtype=float) / 1e6
            rows.append(
                {
                    "case_label": label,
                    "aging_h": aging_h,
                    "pvk_mean_uion": float(np.nanmean(u[pvk])),
                    "pvk_min_uion": float(np.nanmin(u[pvk])),
                    "pvk_max_uion": float(np.nanmax(u[pvk])),
                    "pvk_max_Dtrap": float(np.nanmax(dtrap[pvk])),
                    "pvk_mean_Nt_eff_cm3": float(np.nanmean(nt_cm3[pvk])),
                    "pvk_max_Nt_eff_cm3": float(np.nanmax(nt_cm3[pvk])),
                }
            )
    summary = pd.DataFrame(rows)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(TABLE_DIR / "baseline_pin_spatial_profile_summary.csv", index=False)

    final = summary.loc[summary["aging_h"].eq(1000)].copy()
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Selected spatial-profile summaries at 1000 h equivalent aging.}",
        r"\label{tab:spatial_profile_summary}",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Case & Mean $u_{\mathrm{ion}}$ & Max $u_{\mathrm{ion}}$ & Max $D_{\mathrm{trap}}$ & Mean $N_{t,\mathrm{eff}}$ (cm$^{-3}$) \\",
        r"\midrule",
    ]
    for _, row in final.iterrows():
        lines.append(
            f"{row['case_label']} & {row['pvk_mean_uion']:.3g} & {row['pvk_max_uion']:.3g} & "
            f"{row['pvk_max_Dtrap']:.3g} & {row['pvk_mean_Nt_eff_cm3']:.3e} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (TABLE_DIR / "baseline_pin_spatial_profile_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    configure_style()
    data_by_case = load_cases()
    plot_final_profiles(data_by_case)
    plot_high_stress_evolution(data_by_case["1.00 sun, 400 K"])
    write_conservation_summary(data_by_case)
    print(f"Wrote spatial profile figures to {FIGURE_DIR}")
    print(f"Wrote spatial profile summary to {TABLE_DIR}")


if __name__ == "__main__":
    main()
