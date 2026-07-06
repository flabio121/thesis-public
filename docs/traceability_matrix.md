# Traceability Matrix

## Raw Inputs -> Derived Tables -> Manuscript Artifacts

| Raw source | Derived artifact | Primary manuscript role |
| --- | --- | --- |
| `data/raw/comsol/arch_baseline_pin/time_series/comsol_jv_curves_raw_new.csv` | `data/processed/comsol/comsol_scenario_timeseries.csv` | main electrical-performance dataset |
| `data/raw/comsol/arch_baseline_pin/time_series/comsol_pv_metrics_raw_new.csv` | `data/processed/comsol/comsol_state_timeseries.csv` | state/knob trajectory dataset |
| merged COMSOL tables | `data/processed/comsol/comsol_lifetime_summary.csv` | lifetime table and T80/T90 claims |
| one-only COMSOL cases | `data/processed/comsol/comsol_observability_summary.csv` | active observable-subspace argument |
| COMSOL photogeneration parameters | `data/model_parameters/01_photogeneration_parameters.csv` | Beer-Lambert source-term setup |
| DIT schematic source | `figures/dit_n0_extraction_infographic.png` | DIT workflow and N0 extraction figure |
| thesis presentation motivation graphic | `figures/pptx_ai/si_vs_psc_comparison.png` | qualitative Chapter 1 comparison of commercial silicon PV and emerging perovskite PV |
| processed COMSOL tables | `outputs/figures/comsol_baseline_pce.png` | baseline vs control figure |
| processed COMSOL tables | `outputs/figures/comsol_mechanism_sensitivity.png` | one-only and leave-one-out comparison |
| processed COMSOL tables | `outputs/figures/comsol_metric_signatures.png` | mechanism signature figure |
| processed COMSOL tables | `outputs/figures/comsol_state_trajectories.png` | state/knob evolution figure |
| thesis presentation architecture | `chapters/ch3_comsol_model.tex` Table `lab_comsol_stack`; `figures/pptx_ai/psc_architecture_illumination_1d_mapping.png` | laboratory-to-COMSOL architecture mapping, illumination-side convention, and Beer--Lambert generation-domain schematic |
| verified thesis methods and COMSOL outputs | `journal_submission/main.tex` | concise methodology-and-results manuscript |
| pending corrected-model exports | labeled placeholders in thesis Chapter 7 and journal manuscript | DIT result slot |
| `comsol/Traps_JV.txt` | `outputs/figures/comsol_sweeps/traps_jv.*` | trap-density J--V sweep with PCE annotations |
| `comsol/Res_JV.txt` | `outputs/figures/comsol_sweeps/res_jv.*` | series-resistance J--V sweep with PCE annotations |
| `comsol/ResSH_JV.txt` | `outputs/figures/comsol_sweeps/ressh_jv.*` | shunt-resistance J--V sweep with PCE annotations |
| `data/raw/comsol/arch_baseline_pin/parameter_sweeps/comsol_pscdeg_sweep_001.csv` | `outputs/figures/comsol_parameter_sweep/*`; `outputs/tables/comsol_parameter_sweep_*.csv` | uploaded COMSOL `(Nt0, Rs0, Rsh0)` parameter sweep with J--V examples and extracted PCE/Voc/Jsc/FF metrics; one-parameter slices hold the model reference values, while the best full-factorial point is reported separately |
| `outputs/tables/comsol_parameter_sweep_metrics.csv` | `outputs/figures/comsol_sensitivity/*`; `outputs/tables/comsol_sensitivity_*.csv` | full-factorial grid sensitivity package: local slopes, global effect fractions, response maps, thresholds, and metric ranges |
| `data/raw/comsol/aging/light_heat_85c/comsol_age_light_heat_85c_global_eval.csv` | `outputs/figures/comsol_aging/light_heat_85c/*`; `outputs/tables/comsol_aging/light_heat_85c/*` | canonical light + 85 C heat COMSOL aging export with J--V evolution, PCE/Voc/Jsc/FF metrics, and trap/resistance state diagnostics |
| `data/raw/comsol/aging/light_only/comsol_age_light_only_global_eval.csv` | `outputs/figures/comsol_aging/light_only/*`; `outputs/tables/comsol_aging/light_only/*` | canonical light-only COMSOL aging export with J--V evolution, PCE/Voc/Jsc/FF metrics, and trap/resistance state diagnostics |
| `outputs/tables/comsol_aging/light_only/comsol_age_light_only_scan_metrics.csv`; `outputs/tables/comsol_aging/light_heat_85c/comsol_age_light_heat_85c_scan_metrics.csv` | `outputs/figures/comsol_aging/light_only/comsol_age_light_only_pv_metrics.*`; `outputs/figures/comsol_aging/light_heat_85c/comsol_age_light_heat_85c_pv_metrics.*` | matched-axis PV metric panels showing slower light-only degradation relative to light + 85 C heat |
| `data/raw/comsol/<architecture_slug>/<stress_slug>/*` | `data/processed/comsol/architecture_stress_grid/*`; `outputs/figures/comsol_architecture_stress_grid/*`; `outputs/tables/comsol_architecture_stress_grid/*` | planned architecture- and stress-dependent COMSOL DOE for light/temperature degradation maps and future surrogate training |
| `data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_001.csv` | historical processed `baseline_pin_stress_matrix_jv_001_*` artifacts | superseded one-sun temperature sweep retained for audit history only; replaced by the canonical 6 x 6 light-temperature export |
| `data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_002.csv` | historical processed `baseline_pin_stress_matrix_jv_002_*` artifacts | superseded low-light/Tref-offset export retained for audit history only; not a current missing-data placeholder |
| `data/raw/comsol/arch_baseline_pin/Aging/Stress_matrix_jv_003.csv` | `data/processed/comsol/architecture_stress_grid/baseline_pin_stress_matrix_jv_003_*`; `outputs/figures/comsol_architecture_stress_grid/baseline_pin_stress_matrix_jv_003_*`; `outputs/tables/comsol_architecture_stress_grid/baseline_pin_stress_matrix_jv_003_summary.tex` | canonical flat two-column 6 x 6 light-temperature sweep parsed as 360 time-major J--V curves; PCE and Jsc are usable, while Voc/FF are incomplete for scans that do not cross zero current by 1.25 V |
| `data/raw/comsol/arch_baseline_pin/Aging/profile_grid_light_temperature/*` | `data/processed/comsol/architecture_stress_grid/baseline_pin_profile_grid_summary_long.csv`; `outputs/tables/comsol_architecture_stress_grid/baseline_pin_profile_grid_extrema.tex`; `outputs/tables/comsol_architecture_stress_grid/baseline_pin_spatial_profile_summary.*`; `outputs/figures/comsol_architecture_stress_grid/profile_grid_final_*`; `outputs/figures/comsol_architecture_stress_grid/baseline_pin_spatial_profiles_*` | 6 x 6 baseline p-i-n light-temperature internal-state grid for surrogate-ready state summaries, final-state heatmaps, and selected spatial line-profile figures |
| `data/raw/comsol/arch_baseline_pin/Baseline/Energy Diagram.csv` | `outputs/tables/comsol_architecture_stress_grid/baseline_pin_band_dark_equilibrium_300K.csv`; `outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagram_dark_equilibrium_300K.*` | true dark-equilibrium 300 K baseline band diagram with overlapping electron and hole quasi-Fermi levels |
| `data/raw/comsol/arch_baseline_pin/Aging/stress_light_0_temp_300.csv`; `stress_light_0.6_temp_360.csv`; `stress_light_1_temp_400.csv` | local generated `baseline_pin_band_profiles_long.csv` intermediates; `outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagram_0sun_300K_comsol_style.*`; `outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagrams_selected_cases.*`; `outputs/figures/comsol_architecture_stress_grid/baseline_pin_band_diagram_evolution_1sun_400K.*` | selected COMSOL energy-level exports for architecture-consistent band diagrams with HTL left and ETL right; the dedicated 0-sun/300 K figure mirrors the COMSOL GUI line styling; long profile CSVs may remain untracked due size |
| `docs/data_output_consolidation_plan.md` | cleanup guidance only | canonical-versus-superseded map for thesis data and generated outputs; recommends keeping 001/002 stress-matrix outputs only as audit history |
| processed `Stress_matrix_jv_003` PV metrics, J--V curves, and profile-grid summaries | local `models/surrogate_lite/*.pkl` regenerated by script; committed `models/surrogate_lite/README.md`; `outputs/tables/surrogate_lite/*`; `outputs/figures/surrogate_lite/*` | lite COMSOL-trained surrogate baseline with grouped scenario cross-validation, scalar PCE/PCE-retention/Jsc models, J--V current-density model, DOE coverage, error maps, feature importance, learning curve, and traceability diagrams; large model pickles are ignored for GitHub |
| `docs/ml_surrogate_image_prompts.md` | optional generated conceptual schematics only | prompt provenance for future ChatGPT/image-generation workflow, model-architecture, inverse-diagnosis, DOE-cube, and active-learning schematics; quantitative plots remain script-generated |
| `docs/ml_surrogate_image_prompts.md` + generated image exports | `figures/ml_surrogate/comsol_to_surrogate_workflow_concept.png`; `figures/ml_surrogate/aging_doe_trajectory_concept.png`; `figures/ml_surrogate/forward_surrogate_architecture_concept.png`; `figures/ml_surrogate/inverse_diagnosis_workflow_concept.png` | Chapter 7 conceptual ML workflow, DOE, forward-surrogate, and inverse-diagnosis panels; these are schematic communication figures, not quantitative model-performance plots |
| `comsol/DIT.txt` + PAIOS DIT zip | `outputs/figures/dit/dit_paios_comsol.*` | DIT transient comparison and N0 extraction |
| `data/raw/comsol/arch_baseline_pin/Baseline/DIT.csv` | `outputs/figures/dit/dit_baseline_control.*`; `outputs/tables/dit/dit_baseline_control_summary.csv` | COMSOL dark no-scan DIT baseline-control transient for electronic/capacitive background subtraction before mobile-ion charge integration |

## Archived Reduced-Order Context

| Archived source | Derived artifact | Role |
| --- | --- | --- |
| one-only COMSOL cases + control | `models/reduced_order/comsol_active_observation_basis.csv` | archived reduced-order basis |
| active basis + target scenarios | `data/processed/comsol/comsol_use_case_forecast_summary.csv` | archived screening demonstration |
| processed COMSOL tables + ROM outputs | `outputs/figures/comsol_use_case_forecasts.png` | archived forecasting figure |

## Supporting External Calibration Context

| Supporting source | Derived artifact | Role |
| --- | --- | --- |
| `data/raw/nature_energy_2026/*` | `data/processed/canonical_*.csv` | external calibration and literature context |
| external canonical workflow | `outputs/figures/degradation_timeseries_*.png` | calibration-context figures |
| external canonical workflow | `outputs/tables/arrhenius_fit_summary.tex` | temperature-rate context |

## Local Lab Stress Calibration Context

| Curated source | App/derived artifact | Role |
| --- | --- | --- |
| `data/raw/lab_dropbox/matched_stress_xrf_2025/jv/*` | PSC Degradation Research Explorer organized marts | local JV stress endpoints for COMSOL channel calibration |
| `data/raw/lab_dropbox/matched_stress_xrf_2025/source_metadata/Sample information 251209.pptx` | `data/raw/lab_dropbox/matched_stress_xrf_2025/README.md` | stack and stress-protocol provenance |
| `data/raw/lab_dropbox/matched_stress_xrf_2025/source_manifest.csv` | checksum/provenance audit | trace copied thesis files back to Dropbox originals |
| app copy under `../02_Projects/PSC_Degradation_Research_Explorer/data/Vineeth/XRF matched stress matrix/` | app workspace `COMSOL Calibration` | view baseline-normalized PCE, Voc, Jsc, FF, Rs, and Rsh targets by stack and stress |
| `../02_Projects/PSC_Degradation_Research_Explorer/outputs/comsol_experimental_comparison/*` | `outputs/figures/comsol_experimental_comparison/*`; `outputs/tables/comsol_experimental_comparison/*` | Chapter 6 COMSOL-experimental comparison figures and tables for XRF light-only, heat-only, light-plus-heat, and Exp3 light + 85 C aging targets |

## Script Entry Points

- `scripts/run_comsol_paper_pipeline.py`:
  primary paper workflow
- `scripts/run_psc_degradation_study.py`:
  supporting external calibration workflow
- `scripts/plot_comsol_parameter_sweep.py`:
  uploaded COMSOL parameter-sweep J--V and electronic-metric figures
- `scripts/analyze_comsol_parameter_sensitivity.py`:
  full-factorial electronic sensitivity analysis from the uploaded sweep grid
- `../02_Projects/PSC_Degradation_Research_Explorer/app/streamlit_app.py`:
  PSC degradation app with the COMSOL Calibration workspace
- `scripts/train_lite_surrogates.py`:
  lite COMSOL-trained surrogate models, grouped-CV tables, ML thesis figures,
  and traceability diagrams
