# OptiChain: Methodological Limitations

This document outlines the methodological and empirical boundaries of OptiChain, clearly distinguishing observed historical facts from modeled assumptions.

## 1. Spatial and Temporal Aggregation
- **Regional Zone Granularity**: FAF6 partitions the United States into 134 domestic zones. Each zone represents either an entire metropolitan statistical area (CFS area) or a remainder-of-state geographic block. Consequently, intracity first-mile/last-mile drayage and local access congestion within an MSA are not individually modeled.
- **Annualized Temporal Scope**: The FAF6 benchmark reports annualized freight tonnage and dollar values for the calendar year 2022. It does not provide real-time seasonal variations (e.g., peak agricultural harvest flows or holiday e-commerce surges) or day-to-day dynamic dispatching.

## 2. Transportation Cost Modeling vs. Commercial Tariffs
- **Lack of Commercial Carrier Tariffs in FAF6**: The official FAF6 database provides physical freight tonnage and constant-dollar economic value, but does not publish proprietary commercial freight shipping rates or negotiated carrier tariffs.
- **Modeled Generalized Costs**: To enable linear programming optimization, OptiChain implements a transparent, configurable transportation rate model ($/ton-mile) based on published BTS, AAR, and BLS logistics cost statistics:
  - Truck: $0.180 / ton-mile
  - Rail: $0.045 / ton-mile
  - Water: $0.030 / ton-mile
  - Air: $0.950 / ton-mile
  - Pipeline: $0.025 / ton-mile
- **Circuity Multipliers**: Network distances are calculated from regional geographic centroids using Haversine great-circle distances multiplied by empirical modal circuity factors (Highway: 1.17, Rail: 1.25, Water: 1.45). All cost metrics are explicitly labeled as *Modeled Logistics Expenditure* rather than observed commercial billing records.

## 3. Disruption Scenarios as Exploratory Models
- **Simulation Rather than Historical Reconstruction**: Disruption resilience experiments (corridor closures, capacity reduction percentages, and mode shutdowns) are exploratory stress-testing models designed to evaluate network vulnerability. They do not claim to reconstruct specific historical natural disasters unless explicitly cross-referenced with independent observational damage registries.

## 4. Linearity and Scale Assumptions
- **Constant Returns to Scale**: Standard Linear Programming assumes linear objective functions and constant returns to scale. In real-world freight operations, economies of scale (e.g. unit-train discounts or container vessel size thresholds) can induce concave non-linearities.
