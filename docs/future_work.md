# OptiChain: Future Research and Development Milestones

## 1. Algorithmic and Mathematical Extensions
1. **Mixed-Integer Linear Programming (MILP) with Fixed Charge Arcs**:
   - Introduce binary activation variables $z_{i,j,m} \in \{0, 1\}$ to model fixed infrastructure activation and terminal handling overhead costs:
     $$\min Z = \sum c_{i,j,m} x_{i,j,k,m} + \sum F_{i,j,m} z_{i,j,m}$$
2. **Stochastic and Robust Optimization**:
   - Model freight demand as random variables within budgeted uncertainty sets ($\mathcal{U}$) using Bertsimas and Sim robust optimization to immunize routing decisions against demand volatility.
3. **Multi-Period Dynamic Dispatch & Fleet Balancing**:
   - Extend the single-period static formulation to multi-period dynamic network flows with empty railcar and shipping container repositioning constraints.

## 2. Decarbonization and Environmental Economics
1. **Scope 1 & Scope 3 Freight Greenhouse Gas Emissions Modeling**:
   - Incorporate carbon emission coefficients per ton-mile ($g \text{ CO}_2e / \text{ton-mile}$) by mode:
     - Truck: $\approx 160 \text{ g CO}_2e/\text{ton-mile}$
     - Rail: $\approx 22 \text{ g CO}_2e/\text{ton-mile}$
     - Inland Waterway: $\approx 18 \text{ g CO}_2e/\text{ton-mile}$
2. **Bi-Objective Pareto Frontier Analysis**:
   - Construct multiobjective optimization balancing total transportation expenditure against total environmental carbon emissions ($Z_1 = \text{Cost}, Z_2 = \text{Emissions}$).

## 3. Data Integration and Digital Twin Capabilities
1. **FAF6 Forecast Integration (2030–2050 Projections)**:
   - Ingest high and low macroeconomic growth projections from FAF6 forecast tables to evaluate 30-year capacity investment roadmaps.
2. **Real-time GIS Highway Link Routing**:
   - Integrate the National Highway Planning Network (NHPN) and OpenStreetMap routing APIs to replace centroid desire lines with turn-by-turn physical highway and rail GIS geometry.
