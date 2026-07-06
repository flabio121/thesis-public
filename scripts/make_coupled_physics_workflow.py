#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/pptx_ai/coupled_physics_workflow"


def box(ax: plt.Axes, x: float, y: float, w: float, h: float, title: str, body: str, fc: str) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.25,
        edgecolor="#30343B",
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(x + 0.03, y + h - 0.055, title, ha="left", va="top", fontsize=10, fontweight="bold")
    ax.text(x + 0.03, y + h - 0.125, body, ha="left", va="top", fontsize=7.7, linespacing=1.25, color="#20242A")


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.25,
            color="#2D3748",
            shrinkA=5,
            shrinkB=5,
        )
    )


def mini_jv(ax: plt.Axes, origin: tuple[float, float], size: tuple[float, float]) -> None:
    x0, y0 = origin
    w, h = size
    v = np.linspace(0, 1.12, 160)
    base = 21.0 / (1 + np.exp((v - 0.93) / 0.045))
    aged = 19.4 / (1 + np.exp((v - 0.87) / 0.060)) - 0.45 * v
    ax.plot(x0 + w * v / 1.15, y0 + h * base / 22.5, color="#1976D2", lw=1.7)
    ax.plot(x0 + w * v / 1.15, y0 + h * aged / 22.5, color="#D32F2F", lw=1.7)
    ax.plot([x0, x0 + w], [y0, y0], color="#1F2937", lw=0.8)
    ax.plot([x0, x0], [y0, y0 + h], color="#1F2937", lw=0.8)
    ax.text(x0 + w / 2, y0 - 0.035, "Voltage", ha="center", va="top", fontsize=7)
    ax.text(x0 - 0.035, y0 + h / 2, "Current", ha="right", va="center", fontsize=7, rotation=90)
    ax.text(x0 + 0.02, y0 + h - 0.03, "J-V", ha="left", va="top", fontsize=8, fontweight="bold")


def mini_hysteresis(ax: plt.Axes, origin: tuple[float, float], size: tuple[float, float]) -> None:
    x0, y0 = origin
    w, h = size
    v = np.linspace(0, 1.12, 160)
    reverse = 21.2 / (1 + np.exp((v - 0.94) / 0.045))
    forward = 20.6 / (1 + np.exp((v - 0.90) / 0.055)) - 0.35 * v
    ax.plot(x0 + w * v / 1.15, y0 + h * reverse / 22.5, color="#2E7D32", lw=1.7)
    ax.plot(x0 + w * v / 1.15, y0 + h * forward / 22.5, color="#F57C00", lw=1.7)
    ax.plot([x0, x0 + w], [y0, y0], color="#1F2937", lw=0.8)
    ax.plot([x0, x0], [y0, y0 + h], color="#1F2937", lw=0.8)
    ax.text(x0 + 0.02, y0 + h - 0.03, "hysteresis", ha="left", va="top", fontsize=8, fontweight="bold")
    ax.text(x0 + w - 0.01, y0 + 0.02, "F/R scans", ha="right", va="bottom", fontsize=6.6)


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.6, 4.7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.04, 0.94, "Coupled PSC Degradation Model", fontsize=16, fontweight="bold", ha="left", color="#14213D")
    ax.text(
        0.04,
        0.895,
        "Drift-diffusion, mobile-ion redistribution, trap formation, and resistive aging are solved as one COMSOL workflow.",
        fontsize=8.8,
        ha="left",
        color="#3A3A3A",
    )

    box(ax, 0.05, 0.60, 0.23, 0.22, "Electronic transport", "Poisson and carrier continuity\nwith SRH recombination and\nselective contacts.", "#EAF1FE")
    box(ax, 0.37, 0.60, 0.23, 0.22, "Mobile ions", "Ion redistribution evolves\nbetween scan states and sets\npreconditioned initial states.", "#FFF4C2")
    box(ax, 0.69, 0.60, 0.23, 0.22, "Latent damage", "Trap density, series resistance,\nand shunt resistance evolve\nwith light and temperature.", "#FFEDDE")
    box(ax, 0.21, 0.25, 0.25, 0.20, "Aging protocol", "1 s simulated aging is reported\nas 1 h equivalent aging time.\nJ-V scans are sampled at stops.", "#F4F5F7")
    box(ax, 0.56, 0.25, 0.25, 0.20, "Extracted outputs", "PCE, Jsc, Voc when available,\nFF, J-V curves, band diagrams,\nand spatial state profiles.", "#D8ECBD")

    arrow(ax, (0.28, 0.71), (0.37, 0.71))
    arrow(ax, (0.60, 0.71), (0.69, 0.71))
    arrow(ax, (0.80, 0.60), (0.69, 0.45))
    arrow(ax, (0.46, 0.35), (0.56, 0.35))
    arrow(ax, (0.34, 0.60), (0.33, 0.45))

    mini_jv(ax, (0.065, 0.08), (0.25, 0.13))
    mini_hysteresis(ax, (0.39, 0.08), (0.25, 0.13))
    ax.text(0.72, 0.16, "Traceability", fontsize=8.5, fontweight="bold", ha="left")
    ax.text(0.72, 0.125, "Every thesis figure is generated\nfrom canonical CSV exports and\nversioned scripts.", fontsize=7.3, ha="left", va="top")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT.with_suffix('.png')}")


if __name__ == "__main__":
    main()
