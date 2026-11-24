# OptiChain: Empirical Research Results (FAF6 2022 Benchmark)

This document presents the actual empirical findings obtained from the standardized 10-experiment research framework executed on the FAF6 2022 Benchmark dataset.

## Summary Table of Experimental Results

| Experiment Code | Research Domain | Title | Primary Outcome Metric | Wall-Clock Runtime | Status |
|---|---|---|---|---|---|
| **E1** | Network Science | Historical Freight Network Analysis | Nodes: 20, Edges: 400, Mode HHI: 7,795.97, Comm HHI: 1,454.71 | 0.020s | Optimal |
| **E2** | Linear Programming | Historical Baseline vs. Optimized Allocation | Cost Savings: $1,047,823.32 (2.99% reduction, 3,911 vars) | 0.547s | Optimal |
| **E3** | Transportation LP | Initialization Heuristics vs. MODI Optimum | VAM: $20,294.47 vs. MODI: $20,011.52 (Gap: $282.94; NWCM Gap: $50,940) | 0.010s | Optimal |
| **E4** | Disruption Resilience | Corridor Capacity Reduction (10%, 25%, 50%) | Service Ratio: 100.0% maintained via modal flexibility | 3.042s | Optimal |
| **E5** | Disruption Resilience | Complete Corridor Closure (Top Corridor) | Service Ratio drops to 90.15% (Unmet demand: 283,265k tons) | 1.007s | Optimal |
| **E6** | Disruption Resilience | Rail Mode Disruption (Systemic Outage) | Service Ratio: 98.48% (Truck substitutes 2,626,802k tons) | 1.003s | Optimal |
| **E7** | Capacity Planning | Capital Expansion & Dual Shadow Prices | 386 corridors expanded; Net system benefit: $6,358,678 | 0.458s | Optimal |
| **E8** | Post-Optimality | Cost Sensitivity (+/-10%, +/-20%) | Scaled linearly: +10% cost -> +10.0% objective; +20% -> +20.0% | 4.146s | Optimal |
| **E9** | Post-Optimality | Demand Sensitivity (+/-10%, +/-20%) | Scaled linearly: +10% demand -> +10.0% objective; +20% -> +20.0% | 4.246s | Optimal |
| **E10**| Disruption Resilience | Combined Multi-Disruption Disaster Shock | Service Ratio drops to 89.15% (Unmet: 342,912k tons; Cost surge: +1,009%) | 0.998s | Optimal |

---

## Detailed Analysis of Key Findings

### 1. Network Topology & Concentration (E1)
The empirical FAF6 multimodal freight network exhibits extreme modal concentration:
- **Mode HHI = 7,795.97**: A value substantially above the standard 2,500 threshold, reflecting heavy dependence on highway trucking.
- **Commodity HHI = 1,454.71**: Indicates healthy product diversification across bulk agricultural products (cereal grains, foodstuffs) and manufactured durable goods.
- **Top Freight Hub**: Phoenix AZ CFS region logged the highest total regional throughput (577,099.71 thousand short tons inbound and outbound).

### 2. Economic Efficiency of Multimodal Allocation (E2)
Optimizing freight allocation using linear programming reduces total modeled transportation expenditure from **$35,053,332.97** (historical baseline) to **$34,005,509.65** (optimal allocation), yielding **$1,047,823.32 (2.99%)** in direct logistical savings. The optimization algorithm strategically shifts long-haul non-perishable freight from highway trucking to rail and intermodal options wherever network capacity permits.

### 3. Transportation Heuristic Comparison (E3)
Testing on an identical 4x4 balanced freight matrix revealed dramatic differences in heuristic solution quality:
- **Northwest Corner Method (NWCM)**: Initial cost = $70,951.71 (Gap to global optimum = $50,940.19, a 254% premium).
- **Least Cost Method (LCM)**: Initial cost = $20,241.09 (Gap = $229.56).
- **Vogel's Approximation Method (VAM)**: Initial cost = $20,294.47 (Gap = $282.94).
- **MODI Method**: Reached the proved global optimum of **$20,011.52** in 2 stepping-stone iterations.

### 4. Disruption Vulnerability & Resilience Thresholds (E5, E6, E10)
- Localized corridor severance (E5) had a severe impact: severing the primary intra-hub connector caused the **Resilience Service Ratio to plunge to 90.15%**, leaving 283,265.48 thousand tons of freight stranded.
- A nationwide rail outage (E6) caused 43,825.80 thousand tons of unmet demand, with highway trucking absorbing 2,626,802.20 thousand tons of displaced volume, increasing total system expenditure by 122.43%.
- Under the combined catastrophic disaster scenario (E10: dual corridor closure, waterway outage, 20% fuel surge, and 10% demand surge), the system service ratio dropped to **89.15%**, incurring $377.2M in penalty-adjusted costs (+1,009.25% cost surge).

### 5. Infrastructure Capital Planning Value (E7)
Jointly optimizing freight flows and capital capacity additions identified **386 critical corridors** where dual shadow prices exceeded unit capital expansion costs ($g_{i,j,m}$). Investing $1.71M in targeted capacity expansion reduced system operating costs by $8.07M, yielding a net economic return of **$6.36 million**. The top recommended capital expansion is the **Phoenix AZ -> Los Angeles CA** freight corridor.
