# OptiChain: System Architecture

## 1. Architectural Principles
OptiChain is engineered with strict decoupling between the mathematical optimization engines, data pipelines, persistence layers, and the interactive graphical presentation interface.

```
┌───────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                    │
│   (17 Research & Interactive Modules: Dashboards, Solvers)    │
└───────────────────────────────┬───────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│    Interactive Plotly UI      │       │      PDF / CSV Reporting      │
│  (Maps, Sankey, Centrality)   │       │     (FPDF Academic Output)    │
└───────────────────────────────┘       └───────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│    Mathematical Solvers       │       │       Network Intelligence    │
│  - Simplex / Two-Phase / Big-M│       │  - NetworkX Directed Graph    │
│  - Dual Simplex / Duality     │       │  - Centrality & HHI Metrics   │
│  - Transportation & MODI      │       │  - 134 FAF Zone Coordinates   │
│  - Hungarian Assignment       │       └───────────────────────────────┘
│  - Two-Person Zero-Sum Games  │
│  - SciPy HiGHS Multimodal LP  │
└───────────────────────────────┘
        │                               ▲
        ▼                               │
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     SQLite Persistence        │       │    Data Ingestion Pipeline    │
│  (optichain.db: Models,       │       │  - FAF6.0.csv (1.92M rows)    │
│   Scenarios, Experiments)     │       │  - Metadata Validation        │
│                               │       │  - Parquet Analytical Files   │
└───────────────────────────────┘       └───────────────────────────────┘
```

## 2. Directory Structure and Module Responsibilities
- `src/data/`:
  - `ingestion.py`: Pipeline coordinator for FAF6 data.
  - `cleaning.py`: Casts types, deduplicates records, aggregates flows.
  - `validation.py`: Verifies schema, ranges, geographic codes, and non-negativity.
  - `provenance.py`: Computes cryptographic SHA256 checksums and lineage metadata.
- `src/network/`:
  - `geography.py`: Complete verified coordinate registry for all 134 domestic FAF zones.
  - `graph_builder.py`: Constructs directed NetworkX graphs from flow records.
  - `network_metrics.py`: Computes degree, betweenness, PageRank, and HHI concentration.
- `src/algorithms/`:
  - `simplex.py`: Custom Primal Simplex tableau solver with step logging.
  - `two_phase.py`: Two-phase simplex handling mixed constraints and infeasibility.
  - `big_m.py`: Big-M method with adaptive penalty scaling.
  - `dual_simplex.py`: Dual simplex algorithm for rapid reoptimization.
  - `duality.py`: Primal-dual conversion, shadow prices, and complementary slackness.
  - `sensitivity.py`: Post-optimality allowable ranges and reoptimization.
  - `transportation.py`: NWCM, LCM, and VAM initializations.
  - `modi.py`: Modified Distribution optimality improvement and stepping stone loops.
  - `hungarian.py`: Hungarian assignment for minimum cost or maximum profit.
  - `game_theory.py`: Two-person zero-sum game solver (pure, mixed 2x2, LP).
- `src/models/`:
  - `freight_model.py`: Multimodal freight allocation LP using SciPy HiGHS.
  - `capacity_model.py`: Capacity planning with expansion decision variables.
  - `disruption_model.py`: Network resilience simulation under closures and outages.
- `src/optimization/`:
  - `scenario_engine.py`: Parametric what-if scenario reoptimization.
  - `verification.py`: Independent solver cross-validation.
  - `experiment_runner.py`: Reproducible execution of experiments E1 through E10.
- `src/database/`:
  - `storage.py`: SQLite persistence layer for models, scenarios, and experiments.
- `src/reporting/`:
  - `pdf_report.py`: Academic research PDF generator using FPDF.
  - `csv_export.py`: Clean tabular CSV exporter.
- `src/visualization/`:
  - `maps.py`: Plotly geographic network maps with schematic desire lines.
  - `charts.py`: Plotly commodity bars, mode share donuts, and Sankey flow diagrams.
  - `network_plots.py`: NetworkX graph topology and centrality plots.
- `tests/`: Pytest automated verification suite for all mathematical modules.
- `docs/`: Comprehensive academic and technical documentation.
