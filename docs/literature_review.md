# OptiChain: Literature Review

## 1. Classical Network Flow and Freight Allocation
The mathematical foundation of freight flow modeling originates in the classical transportation problem formulated by Hitchcock (1941) and Koopmans (1949), later generalized to multicommodity minimum-cost network flow problems by Ford and Fulkerson (1962). Ahuja, Magnanti, and Orlin (1993) established fundamental algorithmic complexity benchmarks for polynomial-time primal-dual algorithms and simplex-based network simplex implementations.

In contemporary transportation systems, multimodal freight allocation introduces complex modal choice hierarchies where freight shippers select modes based on generalized logistical expenditure, combining direct carrier freight charges, transit time inventory carrying costs, reliability, and handling risks (de Jong et al., 2013; Tavasszy & de Jong, 2014).

## 2. Freight Analysis Framework (FAF) in Empirical Research
The Freight Analysis Framework (FAF), maintained by the Bureau of Transportation Statistics (BTS) and the Federal Highway Administration (FHWA), is the authoritative public source of macro-level goods movement across the United States. Southworth et al. (2011) and Hwang et al. (2016) documented the analytical methodology used to disaggregate CFS and international trade flows onto domestic highway, rail, and waterway networks. Scholars have utilized FAF data for long-range statewide transportation planning, freight corridor prioritization, and greenhouse gas emissions assessments (Beagan et al., 2007; Holguín-Veras et al., 2014). OptiChain builds directly upon the latest FAF6 2022 Benchmark release.

## 3. Supply Chain Disruption and Network Resilience
Transportation network resilience has emerged as a critical domain of inquiry following major logistical shocks such as extreme weather events, labor disruptions, and infrastructure failures (Faturechi & Miller-Hooks, 2015; Mattsson & Jenelius, 2015). Mathematical models of network resilience generally define resilience as the ability of a logistical system to resist, absorb, adapt to, and recover from disruptive shocks (Bruneau et al., 2003; Rose, 2007). 

In linear programming and mixed-integer programming formulations, resilience is commonly quantified through unmet demand penalties, service level ratios, and rerouting cost premiums (Miller-Hooks et al., 2012). Game-theoretic models of network interdiction (Church et al., 2004; Alderson et al., 2011) analyze max-min attacker-defender games to identify critical infrastructure arcs whose disruption inflicts maximal systemic degradation.

## 4. Duality, Shadow Prices, and Infrastructure Economics
The economic interpretation of dual variables in linear programming originated with Kantorovich (1939) and Dantzig (1963). In transport capacity planning, dual variables on capacity constraints represent marginal shadow prices ($\pi_{i,j,m} = \partial Z^* / \partial u_{i,j,m}$), reflecting the reduction in total systemic operating cost achievable by expanding corridor capacity by one unit (Bazaraa et al., 2010; Hillier & Lieberman, 2021). OptiChain embeds this economic principle directly into its interactive capacity planning module.
