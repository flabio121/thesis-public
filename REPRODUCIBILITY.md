# Reproducibility Guide

## Environment

- Python `>=3.11,<3.14`
- LaTeX with `latexmk`
- Python dependencies from [`requirements.txt`](requirements.txt)

With `uv`:

```powershell
.\scripts\bootstrap_env.ps1
```

Without `uv`:

```powershell
python -m pip install -r requirements.txt
```

## Main Analysis Command

Run the COMSOL-first paper workflow from the repository root:

```powershell
python .\scripts\run_comsol_paper_pipeline.py
```

This reads:

- `data/raw/comsol/arch_baseline_pin/time_series/comsol_jv_curves_raw_new.csv`
- `data/raw/comsol/arch_baseline_pin/time_series/comsol_pv_metrics_raw_new.csv`

And writes:

- `data/processed/comsol/*.csv`
- `outputs/figures/comsol_*.png`
- `outputs/tables/comsol_*.tex`

Archived reduced-order outputs may exist from older workflows, but they are
not required to rebuild the COMSOL-focused thesis.

## Ad-Hoc COMSOL Figure Scripts

The following scripts read raw text exports from `comsol/` and write grouped
outputs under `outputs/figures/`:

```powershell
python .\scripts\plot_traps_jv.py
python .\scripts\plot_res_jv.py
python .\scripts\plot_ressh_jv.py
python .\scripts\plot_dit_paios_comsol.py
python .\scripts\plot_dit_baseline.py
```

J-V sweep outputs are written to `outputs/figures/comsol_sweeps/`. PAIOS/COMSOL
DIT comparison outputs, baseline-control plots, and N0 summaries are written to
`outputs/figures/dit/` and `outputs/tables/dit/`.

## COMSOL Electronic Parameter Sweep

The uploaded COMSOL Global Evaluation sweep for `Nt0`, `Rs0`, and `Rsh0` is
processed separately from the aging-time pipeline:

```powershell
python .\scripts\plot_comsol_parameter_sweep.py
```

This reads:

- `data/raw/comsol/arch_baseline_pin/parameter_sweeps/comsol_pscdeg_sweep_001.csv`

And writes:

- `outputs/tables/comsol_parameter_sweep_metrics.csv`
- `outputs/tables/comsol_parameter_sweep_single_axis_metrics.csv`
- `outputs/figures/comsol_parameter_sweep/*`

The generated figures are included in the thesis as an electronic
parameter-sensitivity study, not as a calibrated lifetime prediction.

For the full-factorial sensitivity package derived from the same sweep metrics:

```powershell
python .\scripts\analyze_comsol_parameter_sensitivity.py
```

This reads:

- `outputs/tables/comsol_parameter_sweep_metrics.csv`

And writes:

- `outputs/tables/comsol_sensitivity_local.csv`
- `outputs/tables/comsol_sensitivity_global_effects.csv`
- `outputs/tables/comsol_sensitivity_metric_ranges.csv`
- `outputs/tables/comsol_sensitivity_threshold_summary.csv`
- `outputs/tables/comsol_sensitivity_key_findings.md`
- `outputs/figures/comsol_sensitivity/*`

Use these outputs when making quantitative sensitivity claims; the
one-parameter sweep figures are mainly for intuition and visual explanation.

## COMSOL Aging Result Exports

Legacy single-condition aging exports are organized by condition slug:

```text
data/raw/comsol/aging/<condition_slug>/
outputs/figures/comsol_aging/<condition_slug>/
outputs/tables/comsol_aging/<condition_slug>/
```

The current light-plus-heat result uses:

- condition slug: `light_heat_85c`
- raw export:
  `data/raw/comsol/aging/light_heat_85c/comsol_age_light_heat_85c_global_eval.csv`
- figures:
  `outputs/figures/comsol_aging/light_heat_85c/`
- tables:
  `outputs/tables/comsol_aging/light_heat_85c/`

The current light-only result uses:

- condition slug: `light_only`
- raw export:
  `data/raw/comsol/aging/light_only/comsol_age_light_only_global_eval.csv`
- figures:
  `outputs/figures/comsol_aging/light_only/`
- tables:
  `outputs/tables/comsol_aging/light_only/`

The derived plots use the current COMSOL aging convention that `1 s`
simulation time corresponds to `1 h` equivalent aging time.

To regenerate the light-only and light-plus-heat PV metric panels with shared
y-axis bounds for direct visual comparison:

```powershell
python .\scripts\plot_comsol_aging_metrics_matched_axes.py
```

## COMSOL Architecture-Stress DOE

Architecture- and stress-dependent COMSOL exports should use the DOE scaffold:

```text
data/raw/comsol/<architecture_slug>/<stress_slug>/
data/processed/comsol/architecture_stress_grid/
outputs/figures/comsol_architecture_stress_grid/
outputs/tables/comsol_architecture_stress_grid/
```

The plan, naming convention, required exports, and initial stress grid are
documented in:

```text
docs/comsol_architecture_stress_doe_plan.md
```

A detailed PDF walkthrough for switching from embedded J--V scan windows to a
two-study aging plus diagnostic J--V setup is available at:

```text
outputs/pdf/comsol_two_study_aging_jv_setup.pdf
```

The editable source is:

```text
docs/comsol_two_study_aging_jv_setup.md
```

Use one architecture folder per device design and one stress folder per
light-temperature condition, for example:

```text
data/raw/comsol/arch_baseline_pin/Aging/
```

Raw COMSOL exports are organized directly by architecture under
`data/raw/comsol/arch_<architecture_slug>/`. Each architecture folder should
contain J--V curves, PV metrics, x-t profile exports, and a small run manifest
before being processed into long-format training and plotting tables.

The current baseline architecture stress-matrix J--V export is processed with:

```powershell
python .\scripts\process_comsol_architecture_stress_jv.py
```

This reads:

```text
data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_001.csv
data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_002.csv
data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_003.csv
```

And writes audit artifacts for every stress-matrix J--V export found:

```text
data/processed/comsol/architecture_stress_grid/baseline_pin_stress_matrix_jv_001_*.csv
data/processed/comsol/architecture_stress_grid/baseline_pin_stress_matrix_jv_002_*.csv
data/processed/comsol/architecture_stress_grid/baseline_pin_stress_matrix_jv_003_*.csv
outputs/tables/comsol_architecture_stress_grid/baseline_pin_stress_matrix_jv_001_*.csv
outputs/tables/comsol_architecture_stress_grid/baseline_pin_stress_matrix_jv_001_summary.tex
outputs/figures/comsol_architecture_stress_grid/baseline_pin_stress_matrix_jv_001_*.{png,svg,pdf}
outputs/figures/comsol_architecture_stress_grid/baseline_pin_stress_matrix_jv_003_*.{png,svg,pdf}
```

`Stress_matrix_jv_001.csv` and `Stress_matrix_jv_002.csv` are superseded
development exports retained for audit history. Current thesis stress-matrix
claims use `Stress_matrix_jv_003.csv`, where COMSOL exported a flat two-column table with
360 concatenated J--V curves. The processor maps this file using time-major
ordering: 36 light-temperature scenarios at each of the same ten aging
checkpoints. The scenario grid is 6 temperatures (`300, 320, 340, 360, 380,
400 K`) by 6 displayed aging light levels (`0, 0.20, 0.40, 0.60, 0.80,
1.00 sun`), where the displayed `0` case is stored as the COMSOL `0.01 sun`
numerical floor.

Chapter 7 quantitative light-temperature stress claims should cite only the
`baseline_pin_stress_matrix_jv_003_*` processed tables and figures. The `001`
and `002` processed outputs may exist in the output folders after a full
processor run, but they are not parallel thesis results.
Its PCE and Jsc trajectories are usable, but Voc and FF are available only for
curves where the 0--1.25 V scan crosses zero current.

The paired profile exports in the same raw folder are large. Keep
`Stress_matrix_output_001.csv` until all needed carrier-generation and profile
variables have been extracted; `Stress_matrix_output_001_lean.csv` is the
smaller working profile export for repeated plotting and diagnostics.

The current 6 x 6 baseline p-i-n light-temperature internal-state profile grid
is organized under:

```text
data/raw/comsol/arch_baseline_pin/Aging/profile_grid_light_temperature/
```

Process it with:

```powershell
python .\scripts\process_comsol_profile_grid.py
python .\scripts\plot_comsol_spatial_profiles.py
```

This writes local generated profile tables and thesis figures:

```text
data/processed/comsol/architecture_stress_grid/baseline_pin_profile_grid_summary_long.csv
outputs/tables/comsol_architecture_stress_grid/baseline_pin_profile_grid_summary_long.csv
outputs/tables/comsol_architecture_stress_grid/baseline_pin_profile_grid_extrema.tex
outputs/figures/comsol_architecture_stress_grid/profile_grid_final_*{png,svg,pdf}
outputs/tables/comsol_architecture_stress_grid/baseline_pin_spatial_profile_summary.{csv,tex}
outputs/figures/comsol_architecture_stress_grid/baseline_pin_spatial_profiles_selected_cases.{png,svg,pdf}
outputs/figures/comsol_architecture_stress_grid/baseline_pin_spatial_profiles_high_stress_time_evolution.{png,svg,pdf}
```

The true dark-equilibrium baseline energy diagram is exported separately:

```text
data/raw/comsol/arch_baseline_pin/Baseline/Energy Diagram.csv
```

Selected newer aging-profile exports include band-edge and quasi-Fermi-level
variables:

```text
data/raw/comsol/arch_baseline_pin/Aging/stress_light_0_temp_300.csv
data/raw/comsol/arch_baseline_pin/Aging/stress_light_0.6_temp_360.csv
data/raw/comsol/arch_baseline_pin/Aging/stress_light_1_temp_400.csv
```

Process them with:

```powershell
python .\scripts\plot_comsol_band_diagrams.py
```

This writes:

```text
data/processed/comsol/architecture_stress_grid/baseline_pin_band_profiles_long.csv
outputs/tables/comsol_architecture_stress_grid/baseline_pin_band_profiles_long.csv
outputs/tables/comsol_architecture_stress_grid/baseline_pin_band_dark_equilibrium_300K.csv
outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagram_dark_equilibrium_300K.{png,svg,pdf}
outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagram_0sun_300K_comsol_style.{png,svg,pdf}
outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagrams_selected_cases.{png,svg,pdf}
outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagram_evolution_1sun_400K.{png,svg,pdf}
```

The long band-profile CSVs are generated intermediates and may remain untracked
because of size; the selected-case figures are the thesis-facing artifacts.
The dark-equilibrium 300 K figure is the correct literature-style band-alignment
reference because its electron and hole quasi-Fermi levels overlap. The
low-light 0-sun/300 K aging-grid figure uses COMSOL-style colors and line types,
but it is a non-equilibrium low-light operating-state diagnostic rather than a
dark-equilibrium band diagram.

COMSOL exports `semi.Ec_e`, `semi.Ev_e`, `semi.Efn_e`, and `semi.Efp_e` in
joules; the plotting script converts these to electron-volts and keeps the
native coordinate direction with the HTL side on the left and ETL side on the
right.

## COMSOL-Experimental Comparison Artifacts

Stress-specific comparison figures and tables from the PSC Degradation
Research Explorer app are copied into the thesis artifact tree:

```text
outputs/figures/comsol_experimental_comparison/
outputs/tables/comsol_experimental_comparison/
```

The source package is:

```text
../02_Projects/PSC_Degradation_Research_Explorer/outputs/comsol_experimental_comparison/
```

These artifacts are used in Chapter 6 as calibration targets for light-only,
heat-only, light-plus-heat, and Exp3 light + 85 C aging comparisons.

## Surrogate Workbench Prototype

The supporting Streamlit app can be launched with:

```powershell
streamlit run .\apps\psc_surrogate_app\streamlit_app.py
```

The current app uses placeholder surrogate logic with current COMSOL seed data.
It is intended to stabilize the data contract, run provenance, export bundle,
inverse-diagnosis interface, uncertainty checks, and active-learning workflow
before trained COMSOL-calibrated surrogate models are available.

## Lite Surrogate Baseline

The current COMSOL light-temperature stress grid can be used to regenerate the
first traceable ML-side baseline:

```powershell
python .\scripts\train_lite_surrogates.py
```

Inputs:

```text
data/processed/comsol/architecture_stress_grid/baseline_pin_stress_matrix_jv_003_pv_metrics_long.csv
data/processed/comsol/architecture_stress_grid/baseline_pin_stress_matrix_jv_003_curves_long.csv
data/processed/comsol/architecture_stress_grid/baseline_pin_profile_grid_summary_long.csv
```

Outputs:

```text
models/surrogate_lite/
outputs/figures/surrogate_lite/
outputs/tables/surrogate_lite/
```

The script uses grouped scenario cross-validation so that complete
light-temperature aging trajectories are held out by fold. It trains a scalar
random-forest branch for PCE, normalized PCE, PCE retention, and Jsc, and a
J-V branch for current density. Voc and FF are intentionally excluded because
the current 1.25 V diagnostic scans do not resolve zero-current crossings for
all scenarios. Generated model `*.pkl` files are local outputs and ignored by
Git; rerun the script to recreate them when inference is needed.

## COMSOL Export Inventory

For fast checks of the exported COMSOL MATLAB model without opening COMSOL:

```powershell
python .\scripts\inspect_comsol_export.py --out .\docs\comsol_export_inventory.md
```

Optional JSON output:

```powershell
python .\scripts\inspect_comsol_export.py --json --out .\outputs\tables\comsol_export_inventory.json
```

## Report Build

```powershell
latexmk -pdf -interaction=nonstopmode main.tex
```

## Journal Manuscript Build

```powershell
Set-Location .\journal_submission
latexmk -pdf -interaction=nonstopmode main.tex
```

The journal manuscript uses current verified figures and retains labeled
placeholders for quantitative DIT extraction until those results are available.

## Optional Legacy Calibration Workflow

The external paper canonicalization workflow remains available:

```powershell
python .\scripts\run_psc_degradation_study.py
```

Use it when you want to regenerate the external Nature Energy 2026 calibration
tables and figures. It is no longer the primary paper workflow.

## Key Deterministic COMSOL Outputs

The paper pipeline should reproduce the following full-coupled baseline values
from the uploaded COMSOL raws:

- `PCE0 approx. 21.35%`
- `PCE3000 approx. 16.51%`
- `T90 approx. 515 h`
- `T80 approx. 2415 h`

The thesis also documents COMSOL-side model components that are configured or
checked manually in COMSOL before export:

- Beer-Lambert generation in the perovskite domain through `Gopt`
- preconditioned mobile-ion initial states through `u_ion`
- DIT pulse extraction through baseline-corrected current integration
- ion-conservation checks through the absorber average of `u_ion`

## Release Checklist

Before publishing the repo, verify:

1. raw COMSOL CSVs are present in `data/raw/comsol/arch_baseline_pin/time_series/`
2. processed outputs were regenerated in the current commit
3. `main.pdf` matches the current artifact set
4. [`CITATION.cff`](CITATION.cff) is up to date
5. the traceability docs still point to the correct files
