# OptiChain: Experimental Design

## 1. Scientific Protocol
The experimental research framework evaluates multimodal freight flow dynamics across 10 controlled experiments (E1 - E10).
All experiments use the verified analytical subset `data/processed/selected_network.parquet` representing 3,911 active corridors between the top 20 national freight hubs across primary freight modes and commodities.

## 2. Experiment Catalog
| ID | Experiment Title | Objective / Hypothesis | Dependent Metrics Recorded |
|---|---|---|---|
| **E1** | Historical Freight Network Analysis | Characterize network topology, hub degree distribution, and concentration. | Nodes, edges, density, mode HHI, commodity HHI, hub throughput. |
| **E2** | Baseline vs Optimized Allocation | Compare historical empirical flows with LP cost-optimal allocation. | Baseline cost, optimized cost, savings amount, savings percentage. |
| **E3** | NWCM vs LCM vs VAM vs MODI | Compare heuristic initializations with global MODI optimum on identical 4x4 matrix. | NWCM cost, LCM cost, VAM cost, MODI optimal cost, optimality gaps. |
| **E4** | Corridor Capacity Reductions (10%, 25%, 50%) | Evaluate resilience degradation under progressive network tightening. | Resilience Service Ratio (%), percentage cost increase (%). |
| **E5** | Complete Corridor Closure | Sever the single highest-volume freight corridor in the system. | Service ratio, unmet demand volume (tons), cost surge ($). |
| **E6** | Transportation Mode Disruption (Rail) | Eliminate rail mode availability system-wide; test highway/water substitution. | Service ratio, truck volume substitution, unmet demand, cost surge. |
| **E7** | Capacity Expansion & Shadow Prices | Jointly optimize flow and capital investments using dual shadow prices. | Transport cost, expansion capital expenditure, number of expanded corridors. |
| **E8** | Cost Sensitivity (+/-10%, +/-20%) | Test stability of optimal basis under fuel and tariff shocks. | Reoptimized objective values, percentage delta relative to baseline. |
| **E9** | Demand Sensitivity (+/-10%, +/-20%) | Evaluate capacity slack under macroeconomic demand contraction or expansion. | Reoptimized objective values, capacity utilization shift. |
| **E10**| Combined Multi-Disruption Scenario | Simulate combined dual-corridor severed + waterway outage + fuel surge + demand spike. | Resilience service ratio, total system cost with penalties, unmet tonnage. |

## 3. Computational Environment & Reproducibility
- Runtime Hardware: Windows 64-bit environment with multi-core x86-64 processor.
- Python Version: 3.12.5.
- Core Optimization Solvers: Custom Primal/Dual Simplex, Two-Phase, Big-M, MODI, Hungarian, and SciPy HiGHS C++ wrapper.
- Execution Trigger: Automated runner (`src/optimization/experiment_runner.py`).
- Output Destinations:
  - `data/experiments/experiments_results.json`
  - `data/experiments/experiments_results.csv`
  - SQLite database `data/optichain.db` (table: `experiments`).
