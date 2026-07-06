# Data and Output Consolidation Plan

This repository is now organized around the COMSOL-first thesis workflow. The
canonical thesis data products should be kept separate from superseded exports,
large local solver files, and presentation-only scratch assets.

## Canonical Thesis Data

- `data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_003.csv`
  - Current 6 x 6 light-temperature J-V export.
  - Parsed as 36 stress scenarios, 10 aging checkpoints, and 360 total curves.
  - Use for Chapter 7 stress-grid J-V metrics and the lite surrogate baseline.
- `data/raw/comsol/arch_baseline_pin/Aging/profile_grid_light_temperature/`
  - Current spatial profile grid for selected internal variables.
  - Use for spatial profiles, stress-grid state summaries, and future inverse
    model labels.
- `data/raw/comsol/arch_baseline_pin/Baseline/Energy Diagram.csv`
  - Dark-equilibrium 300 K band diagram export.
  - Use for baseline band diagram comparisons.
- `data/raw/comsol/arch_baseline_pin/Baseline/DIT.csv`
  - Dark no-scan DIT baseline-control export.
  - Use only as the electronic/capacitive background trace until a matched
    mobile-ion-active DIT export is processed.

## Superseded or Audit-History Data

- `Stress_matrix_jv_001.csv` and `Stress_matrix_jv_002.csv`
  - Superseded development exports.
  - Keep only for audit history if space allows.
  - Do not use in thesis figures, tables, surrogate training, or quantitative
    claims unless a future appendix explicitly compares export evolution.
- Processed/figure outputs with prefixes
  `baseline_pin_stress_matrix_jv_001_` and
  `baseline_pin_stress_matrix_jv_002_`
  - Generated from superseded exports.
  - Candidates for archive or deletion after the final private thesis backup is
    made.

## Generated Outputs

- Keep current thesis outputs under `outputs/figures/` and `outputs/tables/`
  when they are referenced by `main.tex`.
- Treat unreferenced figure variants as scratch unless they document a specific
  thesis revision.
- Regenerate generated outputs from scripts when possible rather than editing
  them by hand.

## Large Local Files

- COMSOL `.mph`, `.lock`, cache, and temporary solver files should not be pushed
  to the public repository.
- Keep final model exports or MATLAB `.m` model history files only when they are
  needed for reproducibility and small enough for practical version control.

## Cleanup Recommendation

Before final submission, archive or delete the superseded 001/002 processed
tables and figures from the working tree if disk space is an issue. The thesis
body and appendix now refer only to the canonical stress-grid export and the
repository traceability documentation.
