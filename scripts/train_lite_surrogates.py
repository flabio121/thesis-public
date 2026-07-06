"""Train and document lite surrogate models from the COMSOL stress grid.

This script is the reproducible entry point for the thesis ML-side artifacts.
It creates grouped-validation metrics, final lightweight random-forest models,
publication-style figures, and traceability metadata from the current COMSOL
light-temperature aging exports. The models are intentionally a first baseline:
they test whether the export contract is usable for surrogate work, not whether
the COMSOL model is already fully calibrated to experiment.
"""

from __future__ import annotations

import json
import math
import pickle
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed/comsol/architecture_stress_grid"
MODEL_DIR = ROOT / "models/surrogate_lite"
TABLE_DIR = ROOT / "outputs/tables/surrogate_lite"
FIGURE_DIR = ROOT / "outputs/figures/surrogate_lite"

PV_METRICS = DATA_DIR / "baseline_pin_stress_matrix_jv_003_pv_metrics_long.csv"
JV_CURVES = DATA_DIR / "baseline_pin_stress_matrix_jv_003_curves_long.csv"
PROFILE_SUMMARY = DATA_DIR / "baseline_pin_profile_grid_summary_long.csv"

SCALAR_FEATURES = ["light_model_suns", "temperature_C", "aging_h", "log1p_aging_h"]
JV_FEATURES = [*SCALAR_FEATURES, "voltage_V"]
SCALAR_TARGETS = ["PCE_pct", "PCE_norm", "PCE_retention_pct", "Jsc_mAcm2"]

TARGET_LABELS = {
    "PCE_pct": "PCE (%)",
    "PCE_norm": "PCE / PCE0",
    "PCE_retention_pct": "PCE retention (%)",
    "Jsc_mAcm2": r"$J_{sc}$ (mA cm$^{-2}$)",
    "current_density_mAcm2": r"$J(V)$ (mA cm$^{-2}$)",
}

FEATURE_LABELS = {
    "light_model_suns": "Aging light (sun)",
    "temperature_C": r"Aging temperature ($^\circ$C)",
    "aging_h": "Equivalent age (h)",
    "log1p_aging_h": r"$\log(1+t)$",
    "voltage_V": "Voltage (V)",
}

PALETTE = {
    "blue": "#1F77E5",
    "orange": "#F57C00",
    "green": "#159A2F",
    "red": "#F0444A",
    "purple": "#7B3FBF",
    "gray": "#555555",
    "light_gray": "#E5E5E5",
}


@dataclass(frozen=True)
class ValidationResult:
    target: str
    model_name: str
    predictions: pd.DataFrame
    metrics: dict[str, object]
    final_model: Pipeline


def apply_style() -> None:
    """Apply a compact Rolston-style manuscript graph theme."""

    sns.set_theme(style="white")
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 8.5,
            "axes.labelsize": 9.5,
            "axes.titlesize": 9.5,
            "axes.linewidth": 1.35,
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.major.width": 1.25,
            "ytick.major.width": 1.25,
            "xtick.major.size": 5.0,
            "ytick.major.size": 5.0,
            "legend.frameon": False,
            "savefig.dpi": 600,
            "svg.fonttype": "none",
        }
    )


def style_axes(ax: plt.Axes, *, grid: bool = False) -> None:
    ax.tick_params(width=1.25, length=5.0)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")
    for spine in ax.spines.values():
        spine.set_linewidth(1.35)
        spine.set_color("black")
    if grid:
        ax.grid(True, color="#D8D8D8", linewidth=0.55, alpha=0.75)
    else:
        ax.grid(False)


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".pdf"):
        fig.savefig(FIGURE_DIR / f"{stem}{suffix}", bbox_inches="tight")
    plt.close(fig)


def add_features(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    light = out["light_suns"].astype(float)
    out["light_model_suns"] = np.where(light <= 0.011, 0.0, light)
    out["log1p_aging_h"] = np.log1p(out["aging_h"].astype(float))
    return out


def light_label(value: float) -> str:
    if value <= 0.011:
        return "0"
    return f"{value:.2f}".rstrip("0").rstrip(".")


def make_model(features: list[str], *, n_estimators: int = 240, random_state: int = 12) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[("num", StandardScaler(), features)],
        remainder="drop",
    )
    regressor = RandomForestRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1,
    )
    return Pipeline([("scale", preprocessor), ("model", regressor)])


def metric_row(
    *,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target: str,
    model_name: str,
    split: str,
    n_groups: int,
    n_folds: int,
) -> dict[str, object]:
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    return {
        "model": model_name,
        "target": target,
        "target_label": TARGET_LABELS[target],
        "split": split,
        "n_samples": int(len(y_true)),
        "n_groups": int(n_groups),
        "n_folds": int(n_folds),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(rmse),
        "r2": float(r2_score(y_true, y_pred)),
    }


def grouped_cv_fit(
    data: pd.DataFrame,
    *,
    features: list[str],
    target: str,
    model_name: str,
    keep_columns: list[str],
    model_path: Path,
) -> ValidationResult:
    required = [*features, target, "scenario_index"]
    fit_data = data.dropna(subset=required).copy()
    groups = fit_data["scenario_index"].astype(int)
    n_groups = groups.nunique()
    n_folds = min(6, n_groups)
    splitter = GroupKFold(n_splits=n_folds)

    parts: list[pd.DataFrame] = []
    y_true_all: list[np.ndarray] = []
    y_pred_all: list[np.ndarray] = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(fit_data, fit_data[target], groups), start=1):
        train = fit_data.iloc[train_idx]
        test = fit_data.iloc[test_idx]
        model = make_model(features, random_state=11 + fold)
        model.fit(train[features], train[target])
        pred = model.predict(test[features])

        pred_frame = test[keep_columns + [target]].copy()
        pred_frame["model"] = model_name
        pred_frame["target"] = target
        pred_frame["target_label"] = TARGET_LABELS[target]
        pred_frame["prediction"] = pred
        pred_frame["fold"] = fold
        pred_frame = pred_frame.rename(columns={target: "actual"})
        parts.append(pred_frame)
        y_true_all.append(test[target].to_numpy())
        y_pred_all.append(pred)

    y_true = np.concatenate(y_true_all)
    y_pred = np.concatenate(y_pred_all)
    final_model = make_model(features, random_state=12)
    final_model.fit(fit_data[features], fit_data[target])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as handle:
        pickle.dump(final_model, handle)

    return ValidationResult(
        target=target,
        model_name=model_name,
        predictions=pd.concat(parts, ignore_index=True),
        metrics=metric_row(
            y_true=y_true,
            y_pred=y_pred,
            target=target,
            model_name=model_name,
            split="group_kfold_by_scenario",
            n_groups=n_groups,
            n_folds=n_folds,
        ),
        final_model=final_model,
    )


def model_feature_importance(model: Pipeline, target: str, features: list[str]) -> pd.DataFrame:
    regressor = model.named_steps["model"]
    importances = regressor.feature_importances_
    return pd.DataFrame(
        {
            "target": target,
            "target_label": TARGET_LABELS[target],
            "feature": features,
            "feature_label": [FEATURE_LABELS[f] for f in features],
            "importance": importances,
        }
    )


def build_dataset_summary(metrics: pd.DataFrame, curves: pd.DataFrame, profiles: pd.DataFrame | None) -> pd.DataFrame:
    curves_per_stress = metrics.groupby("scenario_index")["time_index"].nunique()
    voltage_points = curves.groupby(["scenario_index", "time_index"])["voltage_V"].nunique()
    rows = [
        ("Processed PV metric rows", len(metrics)),
        ("Processed J-V points", len(curves)),
        ("Light-temperature scenarios", metrics["scenario_index"].nunique()),
        ("Aging checkpoints per scenario", int(curves_per_stress.median())),
        ("Voltage points per J-V curve", int(voltage_points.median())),
        ("Displayed light levels", metrics["light_model_suns"].nunique()),
        ("Aging temperatures", metrics["temperature_C"].nunique()),
        ("Resolved Voc/FF curves", int(metrics["valid_jv_metrics"].sum())),
        ("Total diagnostic J-V curves", metrics[["scenario_index", "time_index"]].drop_duplicates().shape[0]),
    ]
    if profiles is not None:
        rows.extend(
            [
                ("Profile-grid summary rows", len(profiles)),
                ("Profile-grid variables", profiles["variable"].nunique()),
            ]
        )
    return pd.DataFrame(rows, columns=["quantity", "value"])


def build_learning_curve(metrics: pd.DataFrame, curves: pd.DataFrame) -> pd.DataFrame:
    """Train-size sensitivity for PCE retention and J-V current."""

    rows: list[dict[str, object]] = []
    tasks = [
        (
            "PCE_retention_pct",
            metrics.dropna(subset=[*SCALAR_FEATURES, "PCE_retention_pct"]).copy(),
            SCALAR_FEATURES,
            "PCE retention (%)",
            110,
        ),
        (
            "current_density_mAcm2",
            curves.dropna(subset=[*JV_FEATURES, "current_density_mAcm2"]).copy(),
            JV_FEATURES,
            r"$J(V)$ (mA cm$^{-2}$)",
            110,
        ),
    ]
    fractions = [0.25, 0.40, 0.60, 0.80, 1.00]
    for target, data, features, target_label, n_estimators in tasks:
        groups = data["scenario_index"].astype(int)
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=31)
        train_idx, test_idx = next(splitter.split(data, groups=groups))
        train_pool = data.iloc[train_idx].copy()
        test = data.iloc[test_idx].copy()
        train_groups = np.array(sorted(train_pool["scenario_index"].unique()))
        test_groups = test["scenario_index"].nunique()
        rng = np.random.default_rng(72)

        for fraction in fractions:
            for repeat in range(4):
                n_train_groups = max(4, int(round(fraction * len(train_groups))))
                if n_train_groups >= len(train_groups):
                    chosen_groups = train_groups
                else:
                    chosen_groups = np.array(sorted(rng.choice(train_groups, size=n_train_groups, replace=False)))
                train = train_pool[train_pool["scenario_index"].isin(chosen_groups)]
                model = make_model(features, n_estimators=n_estimators, random_state=200 + repeat)
                model.fit(train[features], train[target])
                pred = model.predict(test[features])
                rows.append(
                    {
                        "target": target,
                        "target_label": target_label,
                        "train_fraction": fraction,
                        "train_groups": int(len(chosen_groups)),
                        "test_groups": int(test_groups),
                        "train_samples": int(len(train)),
                        "test_samples": int(len(test)),
                        "repeat": repeat + 1,
                        "mae": float(mean_absolute_error(test[target], pred)),
                        "r2": float(r2_score(test[target], pred)),
                    }
                )
    return pd.DataFrame(rows)


def write_latex_metrics_table(metrics: pd.DataFrame) -> None:
    order = ["PCE_pct", "PCE_norm", "PCE_retention_pct", "Jsc_mAcm2", "current_density_mAcm2"]
    table = metrics.set_index("target").loc[order].reset_index()
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Grouped scenario cross-validation metrics for the lite COMSOL-trained surrogate baseline. Scenario grouping keeps complete light-temperature aging trajectories out of the training fold before prediction.}",
        r"\label{tab:surrogate_lite_cv_metrics}",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Target & Samples & Groups & MAE & $R^2$ \\",
        r"\midrule",
    ]
    for _, row in table.iterrows():
        lines.append(
            f"{row['target_label']} & {int(row['n_samples'])} & {int(row['n_groups'])} & "
            f"{row['mae']:.3g} & {row['r2']:.3f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (TABLE_DIR / "surrogate_lite_cv_metrics.tex").write_text("\n".join(lines), encoding="utf-8")


def plot_doe_coverage(metrics: pd.DataFrame) -> None:
    apply_style()
    coverage = (
        metrics.groupby(["temperature_C", "light_model_suns"])["time_index"]
        .nunique()
        .reset_index(name="aging_checkpoints")
    )
    final_age = metrics["aging_h"].max()
    final = metrics.loc[metrics["aging_h"].eq(final_age)].copy()

    temps = sorted(metrics["temperature_C"].unique())
    lights = sorted(metrics["light_model_suns"].unique())
    coverage_matrix = coverage.pivot(index="temperature_C", columns="light_model_suns", values="aging_checkpoints").loc[temps, lights]
    retention_matrix = final.pivot(index="temperature_C", columns="light_model_suns", values="PCE_retention_pct").loc[temps, lights]

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.25), constrained_layout=True)
    sns.heatmap(
        coverage_matrix,
        ax=axes[0],
        cmap=sns.light_palette(PALETTE["blue"], as_cmap=True),
        annot=True,
        fmt=".0f",
        cbar_kws={"label": "J-V scans"},
        linewidths=0.6,
        linecolor="white",
    )
    sns.heatmap(
        retention_matrix,
        ax=axes[1],
        cmap=sns.light_palette(PALETTE["orange"], as_cmap=True),
        annot=True,
        fmt=".1f",
        cbar_kws={"label": "Retention (%)"},
        linewidths=0.6,
        linecolor="white",
    )
    for ax, title in zip(axes, ["Data coverage", f"Final PCE retention ({final_age:g} h)"]):
        ax.set_title(title)
        ax.set_xlabel("Aging light (sun)")
        ax.set_ylabel(r"Aging temperature ($^\circ$C)")
        ax.set_xticklabels([light_label(float(x.get_text())) for x in ax.get_xticklabels()], rotation=0)
        ax.set_yticklabels([f"{float(y.get_text()):.0f}" for y in ax.get_yticklabels()], rotation=0)
        style_axes(ax)
    save_figure(fig, "surrogate_lite_doe_coverage")


def plot_actual_vs_pred(predictions: pd.DataFrame, metrics: pd.DataFrame) -> None:
    apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.7), constrained_layout=True)
    for ax, target in zip(axes.ravel(), SCALAR_TARGETS):
        subset = predictions.loc[predictions["target"].eq(target)].copy()
        row = metrics.loc[metrics["target"].eq(target)].iloc[0]
        ax.scatter(
            subset["actual"],
            subset["prediction"],
            s=22,
            color=PALETTE["blue"],
            edgecolor="black",
            linewidth=0.35,
            alpha=0.82,
        )
        lo = float(np.nanmin([subset["actual"].min(), subset["prediction"].min()]))
        hi = float(np.nanmax([subset["actual"].max(), subset["prediction"].max()]))
        pad = 0.05 * (hi - lo) if hi > lo else 1.0
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="0.20", lw=1.05, ls="--")
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_title(f"{TARGET_LABELS[target]}\nMAE={row['mae']:.3g}, $R^2$={row['r2']:.3f}")
        ax.set_xlabel("COMSOL")
        ax.set_ylabel("Surrogate")
        style_axes(ax, grid=True)
    save_figure(fig, "surrogate_lite_actual_vs_pred")


def plot_jv_examples(predictions: pd.DataFrame) -> None:
    apply_style()
    jv = predictions.loc[predictions["target"].eq("current_density_mAcm2")].copy()
    final_age = jv["aging_h"].max()
    lights = sorted(jv["light_model_suns"].unique())
    temps = sorted(jv["temperature_C"].unique())
    desired = [
        (lights[0], temps[0], final_age),
        (lights[-1], temps[0], final_age),
        (lights[0], temps[-1], final_age),
        (lights[-1], temps[-1], final_age),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.4), constrained_layout=True)
    for ax, (light, temp, age) in zip(axes.ravel(), desired):
        mask = (
            np.isclose(jv["light_model_suns"], light)
            & np.isclose(jv["temperature_C"], temp)
            & np.isclose(jv["aging_h"], age)
        )
        sub = jv.loc[mask].sort_values("voltage_V")
        ax.plot(sub["voltage_V"], sub["actual"], color="black", lw=1.8, label="COMSOL")
        ax.plot(sub["voltage_V"], sub["prediction"], color=PALETTE["orange"], lw=1.8, ls="--", label="Lite surrogate")
        ax.axhline(0, color="0.25", lw=0.8)
        title = f"{light_label(light)} sun, {temp:.0f} $^\\circ$C, {age:g} h"
        ax.set_title(title)
        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel(r"Current density (mA cm$^{-2}$)")
        y_min = min(-5.0, float(sub[["actual", "prediction"]].min().min()) - 0.8)
        y_max = float(sub[["actual", "prediction"]].max().max()) + 1.2
        ax.set_ylim(y_min, y_max)
        ax.legend(loc="best", fontsize=7)
        style_axes(ax, grid=False)
    save_figure(fig, "surrogate_lite_jv_group_cv_examples")


def plot_error_maps(predictions: pd.DataFrame) -> None:
    apply_style()
    final_age = predictions["aging_h"].max()
    scalar = predictions.loc[
        predictions["target"].eq("PCE_retention_pct") & predictions["aging_h"].eq(final_age)
    ].copy()
    scalar["abs_error"] = (scalar["prediction"] - scalar["actual"]).abs()
    pce_error = scalar.pivot_table(
        index="temperature_C",
        columns="light_model_suns",
        values="abs_error",
        aggfunc="mean",
    )

    jv = predictions.loc[predictions["target"].eq("current_density_mAcm2") & predictions["aging_h"].eq(final_age)].copy()
    jv["abs_error"] = (jv["prediction"] - jv["actual"]).abs()
    jv_error = jv.pivot_table(
        index="temperature_C",
        columns="light_model_suns",
        values="abs_error",
        aggfunc="mean",
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.25), constrained_layout=True)
    for ax, matrix, title, cbar_label, fmt in [
        (axes[0], pce_error, "PCE retention absolute error", "Error (percentage points)", ".2f"),
        (axes[1], jv_error, "J-V current-density absolute error", r"Error (mA cm$^{-2}$)", ".2f"),
    ]:
        sns.heatmap(
            matrix,
            ax=ax,
            cmap=sns.light_palette(PALETTE["red"], as_cmap=True),
            annot=True,
            fmt=fmt,
            cbar_kws={"label": cbar_label},
            linewidths=0.6,
            linecolor="white",
        )
        ax.set_title(f"{title}\n{final_age:g} h grouped-CV predictions")
        ax.set_xlabel("Aging light (sun)")
        ax.set_ylabel(r"Aging temperature ($^\circ$C)")
        ax.set_xticklabels([light_label(float(x.get_text())) for x in ax.get_xticklabels()], rotation=0)
        ax.set_yticklabels([f"{float(y.get_text()):.0f}" for y in ax.get_yticklabels()], rotation=0)
        style_axes(ax)
    save_figure(fig, "surrogate_lite_error_maps")


def plot_feature_importance(feature_importance: pd.DataFrame) -> None:
    apply_style()
    order = ["PCE_pct", "PCE_norm", "PCE_retention_pct", "Jsc_mAcm2", "current_density_mAcm2"]
    feature_order = ["light_model_suns", "temperature_C", "aging_h", "log1p_aging_h", "voltage_V"]
    pivot = (
        feature_importance.pivot_table(index="target", columns="feature", values="importance", aggfunc="mean")
        .reindex(index=order, columns=feature_order)
    )
    pivot.index = [TARGET_LABELS[idx] for idx in pivot.index]
    pivot.columns = [FEATURE_LABELS[col] for col in pivot.columns]
    fig, ax = plt.subplots(figsize=(6.8, 3.35), constrained_layout=True)
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=sns.light_palette(PALETTE["green"], as_cmap=True),
        annot=True,
        fmt=".2f",
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Random-forest importance"},
        linewidths=0.6,
        linecolor="white",
    )
    ax.set_xlabel("Input feature")
    ax.set_ylabel("Predicted quantity")
    ax.set_title("Lite surrogate feature importance")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
    style_axes(ax)
    save_figure(fig, "surrogate_lite_feature_importance")


def plot_learning_curve(learning: pd.DataFrame) -> None:
    apply_style()
    summary = (
        learning.groupby(["target", "target_label", "train_groups"], as_index=False)
        .agg(mae_mean=("mae", "mean"), mae_std=("mae", "std"), r2_mean=("r2", "mean"))
        .sort_values(["target", "train_groups"])
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), constrained_layout=True)
    for ax, target, color in [
        (axes[0], "PCE_retention_pct", PALETTE["blue"]),
        (axes[1], "current_density_mAcm2", PALETTE["orange"]),
    ]:
        sub = summary.loc[summary["target"].eq(target)]
        ax.errorbar(
            sub["train_groups"],
            sub["mae_mean"],
            yerr=sub["mae_std"].fillna(0),
            color=color,
            marker="o",
            markersize=4.5,
            lw=1.7,
            capsize=3,
        )
        ax.set_xlabel("Training scenarios")
        ax.set_ylabel("Validation MAE")
        ax.set_title(sub["target_label"].iloc[0])
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        style_axes(ax, grid=True)
    save_figure(fig, "surrogate_lite_learning_curve")


def draw_box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float, text: str, *, fc: str, ec: str = "black", dashed: bool = False) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=ec,
        facecolor=fc,
        linestyle="--" if dashed else "-",
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=8.0,
        fontweight="bold",
        linespacing=1.1,
    )


def draw_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], *, dashed: bool = False) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.1,
        color="black",
        linestyle="--" if dashed else "-",
        shrinkA=3,
        shrinkB=3,
    )
    ax.add_patch(arrow)


def plot_data_traceability_diagram() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(8.0, 3.35))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    boxes = [
        ((0.03, 0.60), 0.18, 0.23, "Raw COMSOL exports\nJ-V 003 file\nprofile grid", "#EAF1FE"),
        ((0.27, 0.60), 0.18, 0.23, "Canonical parsers\n360 J-V curves\n6 x 6 x 10 grid", "#FFF4C2"),
        ((0.51, 0.60), 0.18, 0.23, "Processed long tables\nPV metrics\nJ-V points\nstate summaries", "#FFEDDE"),
        ((0.75, 0.60), 0.20, 0.23, "Traceable thesis assets\nfigures, tables,\nmodel files, metadata", "#D8ECBD"),
        ((0.27, 0.18), 0.18, 0.22, "Feature engineering\nlight, temperature,\nage, voltage", "#FCDAD6"),
        ((0.51, 0.18), 0.18, 0.22, "Grouped validation\nscenario-held-out\ncross-validation", "#F4F5F7"),
        ((0.75, 0.18), 0.20, 0.22, "Documented limits\nVoc/FF excluded\nuntil scans cross 0 A", "#F4F5F7"),
    ]
    for xy, width, height, text, fc in boxes:
        draw_box(ax, xy, width, height, text, fc=fc)
    draw_arrow(ax, (0.21, 0.715), (0.27, 0.715))
    draw_arrow(ax, (0.45, 0.715), (0.51, 0.715))
    draw_arrow(ax, (0.69, 0.715), (0.75, 0.715))
    draw_arrow(ax, (0.60, 0.60), (0.60, 0.40))
    draw_arrow(ax, (0.51, 0.29), (0.45, 0.29))
    draw_arrow(ax, (0.69, 0.29), (0.75, 0.29))
    draw_arrow(ax, (0.60, 0.40), (0.60, 0.60), dashed=True)
    ax.text(0.03, 0.94, "COMSOL-to-surrogate traceability workflow", fontsize=11, fontweight="bold", ha="left")
    ax.text(0.03, 0.895, "Every ML artifact is regenerated from processed COMSOL exports; no manual curve relabeling is used.", fontsize=8.2, ha="left", color="0.25")
    save_figure(fig, "surrogate_lite_data_traceability_workflow")


def plot_model_architecture_diagram() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(8.0, 3.65))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    draw_box(ax, (0.04, 0.62), 0.20, 0.22, "Stress inputs\nlight, temperature,\nage", fc="#EAF1FE")
    draw_box(ax, (0.04, 0.25), 0.20, 0.22, "Electrical input\nvoltage grid\nJ-V scan protocol", fc="#EAF1FE")
    draw_box(ax, (0.34, 0.62), 0.20, 0.22, "Scalar branch\nrandom forest\nscenario CV", fc="#FFF4C2")
    draw_box(ax, (0.34, 0.25), 0.20, 0.22, "J-V branch\nrandom forest\nscenario CV", fc="#FFF4C2")
    draw_box(ax, (0.66, 0.62), 0.24, 0.22, "Metric outputs\nPCE, PCE/PCE0,\nPCE retention, Jsc", fc="#D8ECBD")
    draw_box(ax, (0.66, 0.25), 0.24, 0.22, "Curve output\ncurrent density\nJ(V)", fc="#D8ECBD")
    draw_box(
        ax,
        (0.30, 0.025),
        0.64,
        0.15,
        "Future calibrated extensions:\nuncertainty, inverse state inference, active-learning run selection",
        fc="#F4F5F7",
        dashed=True,
    )
    draw_arrow(ax, (0.24, 0.73), (0.34, 0.73))
    draw_arrow(ax, (0.24, 0.36), (0.34, 0.36))
    draw_arrow(ax, (0.24, 0.73), (0.34, 0.36))
    draw_arrow(ax, (0.54, 0.73), (0.66, 0.73))
    draw_arrow(ax, (0.54, 0.36), (0.66, 0.36))
    draw_arrow(ax, (0.51, 0.25), (0.51, 0.16), dashed=True)
    ax.text(0.04, 0.94, "Lite surrogate architecture", fontsize=11, fontweight="bold", ha="left")
    ax.text(0.04, 0.895, "The current baseline is forward-only and trained on COMSOL stress-grid outputs; inverse diagnosis remains a planned extension.", fontsize=8.2, ha="left", color="0.25")
    save_figure(fig, "surrogate_lite_model_architecture")


def plot_inverse_roadmap_diagram() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(8.0, 3.25))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    y = 0.55
    draw_box(ax, (0.03, y), 0.17, 0.22, "Measured or COMSOL\nJ-V history", fc="#EAF1FE")
    draw_box(ax, (0.25, y), 0.17, 0.22, "Feature extraction\ncurve shape,\nmetric decay", fc="#FFF4C2")
    draw_box(ax, (0.47, y), 0.17, 0.22, "Inverse model\nregularized by\nCOMSOL manifold", fc="#FFEDDE")
    draw_box(ax, (0.69, y), 0.18, 0.22, "Latent states\nDtrap, DRs,\nDRsh, uion", fc="#D8ECBD")
    draw_box(ax, (0.47, 0.16), 0.40, 0.18, "Uncertainty and active learning\nrecommend next COMSOL run where state inference is weak", fc="#F4F5F7", dashed=True)
    draw_arrow(ax, (0.20, y + 0.11), (0.25, y + 0.11))
    draw_arrow(ax, (0.42, y + 0.11), (0.47, y + 0.11))
    draw_arrow(ax, (0.64, y + 0.11), (0.69, y + 0.11))
    draw_arrow(ax, (0.78, y), (0.67, 0.34), dashed=True)
    draw_arrow(ax, (0.56, 0.34), (0.56, y), dashed=True)
    ax.text(0.03, 0.93, "Inverse-diagnosis roadmap", fontsize=11, fontweight="bold", ha="left")
    ax.text(0.03, 0.885, "This is a thesis roadmap diagram, not a trained inverse model claim from the current data.", fontsize=8.2, ha="left", color="0.25")
    save_figure(fig, "surrogate_lite_inverse_diagnosis_roadmap")


def export_error_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    work = predictions.copy()
    work["abs_error"] = (work["prediction"] - work["actual"]).abs()
    grouped = (
        work.groupby(["target", "target_label", "light_model_suns", "temperature_C", "aging_h"], as_index=False)
        .agg(mae=("abs_error", "mean"), n=("abs_error", "size"))
        .sort_values(["target", "temperature_C", "light_model_suns", "aging_h"])
    )
    return grouped


def train_and_validate(metrics: pd.DataFrame, curves: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    results: list[ValidationResult] = []
    feature_importance: list[pd.DataFrame] = []
    scalar_keep = [
        "run_id",
        "scenario_index",
        "light_suns",
        "light_model_suns",
        "temperature_C",
        "time_index",
        "aging_h",
    ]
    for target in SCALAR_TARGETS:
        result = grouped_cv_fit(
            metrics,
            features=SCALAR_FEATURES,
            target=target,
            model_name="rf_scalar_group_cv",
            keep_columns=scalar_keep,
            model_path=MODEL_DIR / f"rf_scalar_{target}.pkl",
        )
        results.append(result)
        feature_importance.append(model_feature_importance(result.final_model, target, SCALAR_FEATURES))

    jv_keep = [
        "run_id",
        "scenario_index",
        "light_suns",
        "light_model_suns",
        "temperature_C",
        "time_index",
        "aging_h",
        "voltage_V",
    ]
    jv_result = grouped_cv_fit(
        curves,
        features=JV_FEATURES,
        target="current_density_mAcm2",
        model_name="rf_jv_group_cv",
        keep_columns=jv_keep,
        model_path=MODEL_DIR / "rf_jv_current_density.pkl",
    )
    results.append(jv_result)
    feature_importance.append(model_feature_importance(jv_result.final_model, "current_density_mAcm2", JV_FEATURES))

    metrics_summary = pd.DataFrame([result.metrics for result in results])
    predictions = pd.concat([result.predictions for result in results], ignore_index=True)
    importance = pd.concat(feature_importance, ignore_index=True)
    return metrics_summary, predictions, importance


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    metrics = add_features(pd.read_csv(PV_METRICS))
    curves = add_features(pd.read_csv(JV_CURVES))
    profiles = pd.read_csv(PROFILE_SUMMARY) if PROFILE_SUMMARY.exists() else None

    metrics_summary, predictions, feature_importance = train_and_validate(metrics, curves)
    learning = build_learning_curve(metrics, curves)
    dataset_summary = build_dataset_summary(metrics, curves, profiles)
    error_summary = export_error_summary(predictions)

    metrics_summary.to_csv(TABLE_DIR / "surrogate_lite_cv_model_metrics.csv", index=False)
    metrics_summary.to_csv(TABLE_DIR / "surrogate_lite_model_metrics.csv", index=False)
    predictions.to_csv(TABLE_DIR / "surrogate_lite_group_cv_predictions.csv", index=False)
    feature_importance.to_csv(TABLE_DIR / "surrogate_lite_feature_importance.csv", index=False)
    learning.to_csv(TABLE_DIR / "surrogate_lite_learning_curve.csv", index=False)
    dataset_summary.to_csv(TABLE_DIR / "surrogate_lite_dataset_summary.csv", index=False)
    error_summary.to_csv(TABLE_DIR / "surrogate_lite_error_by_condition.csv", index=False)
    write_latex_metrics_table(metrics_summary)

    metadata = {
        "artifact_family": "lite_surrogate_baseline",
        "input_metrics": str(PV_METRICS.relative_to(ROOT)),
        "input_curves": str(JV_CURVES.relative_to(ROOT)),
        "input_profile_summary": str(PROFILE_SUMMARY.relative_to(ROOT)),
        "validation": "GroupKFold by scenario_index; complete light-temperature aging scenarios are held out by fold.",
        "final_models": "RandomForestRegressor pipelines retrained on all valid rows after grouped validation.",
        "features_scalar": SCALAR_FEATURES,
        "features_jv": JV_FEATURES,
        "targets_scalar": SCALAR_TARGETS,
        "target_jv": "current_density_mAcm2",
        "excluded_targets": {
            "Voc_V": "Incomplete zero-current crossings because the current export ends at 1.25 V.",
            "FF": "Depends on resolved Voc; excluded until diagnostic scans extend beyond the zero-current crossing for all conditions.",
        },
        "display_conventions": [
            "Stored 0.01 sun aging cases are encoded as light_model_suns = 0.0 for labels and ML features.",
            "Temperatures are stored from the COMSOL K grid as Celsius values in the processed tables.",
        ],
        "caveat": "This is a first lightweight surrogate baseline and not a calibrated experimental predictive model.",
    }
    (TABLE_DIR / "surrogate_lite_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    plot_data_traceability_diagram()
    plot_model_architecture_diagram()
    plot_inverse_roadmap_diagram()
    plot_doe_coverage(metrics)
    plot_actual_vs_pred(predictions, metrics_summary)
    plot_jv_examples(predictions)
    plot_error_maps(predictions)
    plot_feature_importance(feature_importance)
    plot_learning_curve(learning)

    print(metrics_summary.to_string(index=False))


if __name__ == "__main__":
    main()
