# OptiChain: Problem Statement

## 1. Context and Motivation
Freight transportation is the structural backbone of modern economic supply chains. In the United States, over 19.6 billion short tons of freight valued at approximately $24.8 trillion move across complex multimodal logistical corridors annually. The Freight Analysis Framework Version 6 (FAF6), developed jointly by the Bureau of Transportation Statistics (BTS) and the Federal Highway Administration (FHWA), integrates trade and shipping data from the Commodity Flow Survey (CFS), international trade registries, and agricultural databases into a comprehensive origin-destination matrix across 134 domestic economic zones.

Despite the wealth of empirical data provided by FAF6, public transport planners, supply chain directors, and operations research analysts face acute challenges in:
1. **Multimodal Flow Allocation**: Determining cost-optimal routing across competitive transportation modes (truck, rail, water, air, pipeline, and intermodal) subject to physical network capacities, regional commodity supply limits, and local consumption requirements.
2. **Infrastructure Capacity Bottlenecks**: Identifying binding logistical corridors and economically quantifying the marginal shadow price of incremental capacity expansions.
3. **Disruption Vulnerability and Systemic Resilience**: Stress-testing supply networks against catastrophic corridor closures (e.g., bridge failures, canal blockages, weather extremes) or systemic modal outages (e.g., rail strikes, port congestion, diesel price surges).

## 2. Formal Problem Statement
Given a directed multimodal freight network $G = (V, E, M)$ where $V$ represents 134 domestic FAF6 freight regions, $E$ represents observable origin-destination transport corridors, and $M$ represents available transportation modes:
1. Formulate a primal-dual Linear Programming (LP) model that minimizes total modeled transportation expenditure while strictly satisfying regional commodity supply limits, origin-destination demands, and modal corridor capacity boundaries.
2. Evaluate marginal economic capacity values via dual shadow prices ($\pi_{i,j,m} = \frac{\partial Z^*}{\partial u_{i,j,m}}$) to prioritize capital expansion investments.
3. Quantify network resilience under exogenous shocks by incorporating unmet-demand shortage penalties and computing the **Resilience Service Ratio**:
   $$\text{Service Ratio} = \frac{\sum_{i,j,k,m} x_{i,j,k,m}}{\sum_{i,j,k} d_{i,j,k}} \times 100\%$$
4. Integrate educational classical Operations Research modules (Primal Simplex, Two-Phase, Big-M, Dual Simplex, NWCM, LCM, VAM, MODI, Hungarian Assignment, and Zero-Sum Game Theory) to bridge academic syllabus innovation with empirical industrial logistics.
