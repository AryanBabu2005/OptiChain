# OptiChain — Multimodal Freight Network Optimization & Disruption Resilience Platform

> **"Understand the Network. Optimize the Flow. Strengthen Resilience."**

An academic, research-grade software platform that formulates and solves multimodal freight allocation problems, evaluates infrastructure capacity bottlenecks via linear programming shadow prices, and stress-tests systemic supply chain resilience against real-world disruptions using the official **Freight Analysis Framework Version 6 (FAF6.0)** 2022 Benchmark database published by the **U.S. Bureau of Transportation Statistics (BTS)** and the **Federal Highway Administration (FHWA)**.

Designed and developed as a semester-long capstone in **Operations Research, Mathematical Innovation, and Network Science**.

---

## 1. Project Overview & Research Objectives

The national freight transportation network is the physical backbone of the economy, moving over 19.6 billion tons of cargo valued at $24.8 trillion annually across highway, rail, inland waterway, pipeline, and air corridors. However, extreme modal dependence on long-haul trucking (accounting for over 87% of domestic tonnage) leaves the supply chain vulnerable to fuel price shocks, labor shortages, infrastructure degradation, and catastrophic chokepoint closures (e.g., the 2024 Baltimore Key Bridge collapse, Mississippi River low-water barge restrictions, or rail labor stoppages).

OptiChain addresses these challenges through a unified mathematical and computational framework:

1. **Empirical Network Ingestion & Centrality Analysis**:
   - Ingests the complete 2022 FAF6 benchmark (1,921,887 raw flow records across 134 domestic regions, 42 SCTG commodity groups, and 8 modes).
   - Computes topological network metrics (in/out-degree, flow-weighted throughput, betweenness centrality, PageRank) and market concentration indices (Herfindahl-Hirschman Index — HHI).
2. **Multimodal Linear Programming Optimization**:
   - Formulates a large-scale linear program minimizing modeled logistics costs subject to regional supply conservation, destination demand satisfaction, and corridor capacity bounds.
   - Solved with SciPy HiGHS backend with full primal and dual extraction.
3. **Capacity Planning & Dual Shadow Price Valuation**:
   - Computes dual marginal values ($\pi_{i,j,m} = \partial Z^* / \partial u_{i,j,m}$) to identify binding infrastructure bottlenecks.
   - Solves a joint flow and continuous capacity expansion model ($y_{i,j,m}$) balancing transportation savings against capital expansion costs ($g_{i,j,m}$).
4. **Freight Disruption Simulator & Resilience Stress Testing**:
   - Evaluates system survivability under 8 distinct disruption classes using unmet-demand penalty formulations.
   - Quantifies the **Resilience Service Ratio** and traces modal substitution dynamics.
5. **Core Operations Research Syllabus Implementation (Units I–IV)**:
   - Built-from-scratch algorithms with step-by-step tableau inspection:
     - **Unit I**: Primal Simplex with tableau history, entering/leaving selection (Bland's rule), pivot operations, and degeneracy detection.
     - **Unit II**: Two-Phase Simplex, Big-M method, Dual Simplex, and Strong Duality verification ($c^T x^* = b^T y^*$) with complementary slackness checks.
     - **Unit III**: Transportation models (NWCM, LCM, VAM) with automated dummy balancing and MODI (u-v method) stepping-stone global optimality improvement.
     - **Unit IV**: Hungarian Assignment (Kuhn-Munkres) for square and rectangular cost matrices, and Two-Person Zero-Sum Game Theory (saddle point, 2x2 analytical, and general LP minimax).
6. **Green Logistics & Emissions Abatement**:
   - EPA SmartWay and GLEC framework Scope 3 carbon emission modeling ($CO_2$ grams per ton-mile).
   - Bi-objective Pareto Frontier tracing the trade-off between logistical cost and carbon emissions.

---

## 2. Distinction of Data Layers

To maintain academic rigor and transparency, OptiChain strictly categorizes every variable into three clear tiers:
- **Observed Data**: Directly extracted from official BTS FAF6.0 tables (`tons_2022`, `value_2022`, origin/destination FAF codes, SCTG commodity classifications, recorded transport modes).
- **Derived Metrics**: Mode-adjusted routing distances computed using geographic centroid Haversine equations scaled by empirical **modal circuity factors** (Highway: 1.17, Rail: 1.25, Water: 1.45, Air: 1.05).
- **Assumed Parameters**: Mode-specific cost rates ($/ton-mile, e.g. Truck $0.18, Rail $0.045, Water $0.025, Air $0.85) derived from transportation economics literature (BTS, Texas A&M Transportation Institute), fully editable by the user for scenario analysis.

---

## 3. Directory Layout

```
OptiChain/
  ├── app.py                      # Main Streamlit application entrypoint
  ├── requirements.txt            # Python dependencies (Streamlit, Pandas, NumPy, SciPy, NetworkX, Plotly, FPDF)
  ├── pytest.ini                  # Pytest configuration
  ├── README.md                   # Complete documentation and viva defense guide
  │
  ├── data/
  │   ├── raw/                    # FAF6.0.csv, FAF6 User Guide.pdf
  │   ├── metadata/               # FAF6_Metadata.xlsx
  │   ├── processed/              # Snappy Parquet files (cleaned, aggregated flows, selected network, demo)
  │   ├── experiments/            # experiments_results.json, .csv, and research PDF report
  │   └── optichain.db            # SQLite database for saved models and scenarios
  │
  ├── src/
  │   ├── data/                   # Ingestion, cleaning, validation, and SHA-256 provenance tracker
  │   ├── network/                # 134 FAF zone centroids, NetworkX graph builder, centrality metrics
  │   ├── algorithms/             # Simplex, Two-Phase, Big-M, Dual Simplex, Duality, Transportation, MODI, Hungarian, Game Theory
  │   ├── models/                 # Multimodal Freight LP, Capacity Expansion, Disruption Simulator, Emissions Engine
  │   ├── optimization/           # Scenario engine, verification engine, and 10-experiment runner
  │   ├── reporting/              # Multi-page FPDF academic PDF generator and CSV exporter
  │   ├── visualization/          # Plotly choropleth maps, Sankey diagrams, scatter plots, network layouts
  │   ├── database/               # SQLite CRUD persistence layer
  │   └── ui/                     # Modular Streamlit page renderers
  │
  ├── tests/                      # Automated Pytest unit test suites (19 test cases)
  └── docs/                       # Academic documentation compendium (15 Markdown reports)
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12 (64-bit recommended)
- Git

### Step-by-Step Setup
1. **Navigate to the Workspace Directory**:
   ```bash
   cd c:\Users\babua\OptiChain_Math
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Data Pipeline**:
   The ingestion pipeline automatically runs on first startup, or you can invoke it directly from Python:
   ```bash
   python -c "from src.data.ingestion import FAF6IngestionPipeline; FAF6IngestionPipeline().run_pipeline()"
   ```

---

## 5. Running the Application

Launch the interactive Streamlit research platform:
```bash
streamlit run app.py
```
Then open your web browser to `http://localhost:8501`.

---

## 6. Automated Verification & Testing

OptiChain includes a comprehensive automated test suite validating all mathematical algorithms, tableau pivots, duality theorems, dummy balancing, and data pipeline integrity:
```bash
python -m pytest -v
```
All 19 test cases execute and verify mathematical correctness in under 5 seconds.

---

## 7. Viva / Demonstration Script (5–10 Minute Walkthrough)

When presenting OptiChain to an examiner, professor, or project evaluation committee, follow this structured, human-centered walkthrough:

### Minute 1: The Problem & Real Data Ingestion
- Open the application to **"Executive Dashboard"**.
- Explain the motivation: *"The US moves nearly 20 billion tons of freight annually, but over 87% is concentrated on highways. Our goal is to model, optimize, and stress-test this multimodal network using real data."*
- Highlight the **Status Banners**: Show how the platform clearly distinguishes observed FAF6 data, derived Haversine distances with modal circuity, and assumed cost parameters.
- Navigate to **"Data Provenance & Checksums"**: Show the SHA-256 hash (`bbe7e2c1...`) matching the official 1.92M-record raw CSV from BTS/FHWA, and point out the zero-duplicate, zero-null validation report.

### Minute 2: Freight Network Intelligence & Concentration
- Navigate to **"Freight Network Graph"**.
- Point out the **Herfindahl-Hirschman Index (HHI)**:
  - Mode HHI = **7,795.97** (severe concentration, well above the DOJ's 2,500 threshold).
  - Commodity HHI = **1,454.71** (diversified bulk and manufactured goods).
- Show the **Network Topology Graph** and explain **Betweenness Centrality**:
  - Explain that nodes like Chicago, Memphis, and Dallas act as critical transshipment bridges; disruptions here propagate nationwide.

### Minute 3: Multimodal LP Optimization
- Navigate to **"Multimodal Optimizer"**.
- Select the `selected_network.parquet` (3,911 corridors connecting the top 20 domestic hubs).
- Click **"Execute Multimodal Linear Program"**.
- Show the results:
  - System saves **~$1.05 million (2.99%)** by reallocating non-perishable freight from highway trucks to rail and water corridors where capacity permits.
  - Review the dual variables and reduced costs in the extracted solution table.

### Minute 4: Capacity Planning & Dual Shadow Prices
- Navigate to **"Capacity Planning & Shadow Prices"**.
- Explain how the dual shadow prices ($\pi_{i,j,m} = -\partial Z / \partial u_{i,j,m}$) reveal the marginal value of corridor expansion.
- Show the automated expansion recommendations: 386 corridors have shadow prices higher than their unit expansion cost, generating **$6.36M in net economic benefit**.

### Minute 5: Disruption Resilience & Stress Testing
- Navigate to **"Disruption Simulator"**.
- Select the **"Baltimore Key Bridge Collapse (2024)"** or **"Nationwide Rail Labor Strike"** preset.
- Click **"Simulate Disruption Impact"**.
- Show the resulting impact metrics:
  - **Resilience Service Ratio**: Drops to 90.15% (showing 283,265 kilotons of unmet demand).
  - **Mode Substitution**: Traces the spillover of cargo onto highways, driving up congestion and costs.

### Minute 6: Operations Research Syllabus Workbenches (Units I–IV)
- Open **"Syllabus Units I–IV Workbench"**:
  - **Unit I (Simplex Stepper)**: Step through tableau iterations; highlight the entering variable (most negative reduced cost) and leaving variable (minimum ratio test), demonstrating Bland's rule against cycling.
  - **Unit II (Duality & Two-Phase)**: Show Phase I artificial variable elimination ($W \to 0$) and strong duality equality ($c^T x^* = b^T y^*$).
  - **Unit III (Transportation & MODI)**: Compare NWCM ($70,951), LCM ($23,710), and VAM ($20,294) on the grain transport matrix; run MODI to reach the global optimum ($20,011) via stepping-stone loops.
  - **Unit IV (Assignment & Game Theory)**: Demonstrate Hungarian 1-to-1 carrier depot dispatching ($12,400) and the two-person zero-sum Minimax interdiction saddle point.

### Minute 7: Green Logistics & PDF Report Export
- Open **"Green Logistics & Emissions"**: Show the Cost vs. $CO_2$ Pareto Frontier and the Marginal Abatement Cost ($38.50/ton $CO_2$).
- Open **"Experiment Battery (E1–E10)"**: Show the 10 reproducible experiments.
- Click **"Download Academic Research Report (PDF)"** to showcase the automatically generated multi-page formal report.

---

## 8. Academic References

1. **U.S. Bureau of Transportation Statistics & Federal Highway Administration (2024)**. *Freight Analysis Framework (FAF6) Version 6.0 User Guide and 2022 Benchmark Dataset*. U.S. Department of Transportation.
2. **Hillier, F. S., & Lieberman, G. J. (2021)**. *Introduction to Operations Research* (11th ed.). McGraw-Hill Education.
3. **Taha, H. A. (2017)**. *Operations Research: An Introduction* (10th ed.). Pearson.
4. **Bazaraa, M. S., Jarvis, J. J., & Sherali, H. D. (2010)**. *Linear Programming and Network Flows* (4th ed.). John Wiley & Sons.
5. **EPA SmartWay Transport Partnership (2023)**. *Freight Emission Factors and Accounting Methodologies*. U.S. Environmental Protection Agency.
6. **NetworkX Developers (2024)**. *NetworkX: Network Analysis in Python*. Software documentation.
