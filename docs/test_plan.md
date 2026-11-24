# OptiChain: Comprehensive Automated Test Plan

## 1. Quality Assurance Strategy
The OptiChain platform implements an automated test suite executed via `pytest`. The testing protocol ensures mathematical soundness across University Syllabus Units I–IV, validates FAF6 data pipelines, and cross-verifies custom algorithms against SciPy/HiGHS.

## 2. Test Matrix and Verification Modules

### Unit I: Simplex Algorithm Tests (`tests/test_core_math.py`)
- `test_bounded_maximization`: Standard bounded maximization ($\max Z = 3x_1 + 5x_2$); verifies optimal vertex $[2, 6]$, objective $Z^* = 36.0$.
- `test_bounded_minimization`: Minimization via objective negation; verifies $Z^* = -36.0$.
- `test_unbounded_problem`: Detects non-positive pivot columns and asserts `status == "unbounded"`.
- Degeneracy & Alternate Optima: Checks $b_i = 0$ in basic columns and zero reduced costs on non-basic variables.

### Unit II: Artificial Variables, Infeasibility & Duality
- `test_two_phase_and_big_m_feasibility`: Verifies Phase I artificial minimization and Phase II optimality on mixed $\ge, =, \le$ constraints ($Z^* = 3.4$).
- `test_infeasible_problem_detection`: Constructs contradictory constraints ($x_1 + x_2 \le 2$ and $x_1 + x_2 \ge 4$); asserts `status == "infeasible"`.
- `test_duality_and_complementary_slackness`: Verifies Strong Duality ($c^T x^* = b^T y^*$), zero duality gap, and Complementary Slackness:
  $$(b_i - A_i x^*) \cdot y_i^* = 0 \quad \text{and} \quad (c_j - A_j^T y^*) \cdot x_j^* = 0$$

### Unit III: Transportation & MODI Optimality
- `test_transportation_initializations_and_modi`: Runs NWCM, LCM, and VAM on balanced $3 \times 4$ cost matrix; confirms $Z_{\text{VAM}} \le Z_{\text{NWCM}}$.
- MODI stepping-stone optimization: Tests initial BFS and asserts global optimality reached with all opportunity costs $\Delta_{ij} \ge 0$.
- `test_unbalanced_transportation`: Tests supply-demand imbalance; verifies automatic creation of dummy column/row with cost 0.

### Unit IV: Assignment & Game Theory
- `test_hungarian_assignment`: Solves $4 \times 4$ cost matrix; verifies optimal matching with $Z^* = 13.0$.
- Brute-force verification: Validates Hungarian assignment against exhaustive permutation search on all $4! = 24$ permutations.
- `test_rectangular_assignment_with_dummies`: Tests $2 \times 3$ matrix; verifies optimal dummy assignment.
- `test_pure_strategy_saddle_point_game`: Tests $3 \times 3$ matrix with saddle point; confirms $\text{Maximin} = \text{Minimax} = 3.0$.
- `test_mixed_strategy_game`: Solves Matching Pennies game; verifies $p^* = [0.5, 0.5]$, $q^* = [0.5, 0.5]$, $V = 0.0$.

### Data Ingestion & Integration Tests (`tests/test_data_pipeline.py`)
- Schema completeness: Verifies 11 required FAF6 columns.
- Duplicate detection: Verifies 0 duplicate records across all 9 categorical dimensions.
- Range checks: Verifies non-negative tonnage and values.
- Regional code integrity: Confirms all origin/destination codes exist within the 134 domestic FAF zones.

## 3. Execution Commands
```bash
# Execute entire test battery
python -m pytest -v

# Run mathematical unit tests specifically
python -m pytest -v tests/test_core_math.py
```
