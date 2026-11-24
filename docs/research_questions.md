# OptiChain: Research Questions

This research investigates the following core scientific questions at the intersection of Operations Research, Transportation Economics, and Network Science:

### RQ1: Multimodal Freight Flow Optimization
*To what extent can mathematically optimized multimodal freight allocation reduce national modeled logistics expenditure compared to historical empirical baseline flow distributions?*
- How do modal substitution rates (shifting volume from highway trucking to rail or inland waterways) vary across different distance bands and commodity types?
- What are the physical and capacity impediments preventing greater utilization of low-cost, low-emission rail and barge modes?

### RQ2: Dual Shadow Prices & Infrastructure Capacity Planning
*How can linear programming duality and dual variable shadow prices ($\pi_{i,j,m}$) be leveraged to detect critical freight network bottlenecks and prioritize corridor expansion capital investments?*
- Which freight corridors exhibit positive shadow prices, indicating that an additional ton of capacity yields substantial marginal system cost savings?
- What is the financial threshold where unit capital expansion costs ($g_{i,j,m}$) exceed the marginal dual value of capacity?

### RQ3: Disruption Resilience and Systemic Network Vulnerability
*How does regional freight connectivity degrade under severe localized corridor closures versus nationwide modal outages, and what is the optimal adaptive reallocation response?*
- How does the **Resilience Service Ratio** respond to systematic capacity reductions (10%, 25%, 50%, and 100% closures)?
- In the presence of high unmet-demand penalties ($P = \$1,000/\text{ton}$), what alternative routing corridors absorb displaced cargo, and what are the resulting economic cost increases?

### RQ4: Algorithmic Efficiency and Educational Foundations
*How do classical Operations Research initialization heuristics (Northwest Corner, Least Cost Method, Vogel's Approximation Method) compare in initial solution quality and distance to the MODI global optimum on empirical freight matrices?*
- How do custom step-by-step Simplex tableau implementations compare against interior-point and dual-simplex C/C++ solvers (SciPy HiGHS) in accuracy, degeneracy handling, and solution stability?
- How can competitive zero-sum game models characterize the strategic equilibrium between a logistics planner and an adversary or catastrophic disruption event?
