# OptiChain: Mathematical Formulations

## 1. Multimodal Freight Allocation Problem (Core LP)

### Sets and Indices
- $i \in I$: Freight origin regions ($|I| \le 134$).
- $j \in J$: Freight destination regions ($|J| \le 134$).
- $k \in K$: Commodity categories ($|K| \le 42$).
- $m \in M$: Transportation modes ($|M| \le 8$).

### Decision Variables
- $x_{i,j,k,m} \ge 0$: Freight tonnage (thousand tons) allocated from origin $i$ to destination $j$ for commodity $k$ using mode $m$.

### Parameters
- $c_{i,j,m}$: Modeled unit transportation cost (\$/ton) on corridor $(i, j)$ via mode $m$:
  $$c_{i,j,m} = r_m \cdot d_{i,j,m}$$
  where $r_m$ is the mode-specific ton-mile rate (\$/ton-mile) and $d_{i,j,m}$ is the circuity-adjusted corridor route distance in miles.
- $d_{i,j,k}$: Observed freight demand (thousand tons) for commodity $k$ moving from origin $i$ to destination $j$.
- $S_{i,k}$: Total available supply of commodity $k$ at origin region $i$:
  $$S_{i,k} = \theta_S \sum_{j} d_{i,j,k} \quad (\theta_S \ge 1.0)$$
- $u_{i,j,m}$: Upper physical capacity limit (thousand tons) on corridor $(i, j)$ for mode $m$:
  $$u_{i,j,m} = \theta_C \sum_{k} x_{i,j,k,m}^{\text{observed}} \quad (\theta_C \ge 1.0)$$

### Formulation
$$\min_{x} Z = \sum_{i \in I} \sum_{j \in J} \sum_{k \in K} \sum_{m \in M} c_{i,j,m} \cdot x_{i,j,k,m}$$

Subject to:
1. **Demand Satisfaction Constraints**:
   $$\sum_{m \in M} x_{i,j,k,m} = d_{i,j,k} \quad \forall i \in I, j \in J, k \in K \quad [\lambda_{i,j,k}]$$
2. **Regional Supply Capacity Constraints**:
   $$\sum_{j \in J} \sum_{m \in M} x_{i,j,k,m} \le S_{i,k} \quad \forall i \in I, k \in K \quad [\mu_{i,k}]$$
3. **Modal Corridor Capacity Constraints**:
   $$\sum_{k \in K} x_{i,j,k,m} \le u_{i,j,m} \quad \forall i \in I, j \in J, m \in M \quad [\pi_{i,j,m}]$$
4. **Non-negativity**:
   $$x_{i,j,k,m} \ge 0 \quad \forall i, j, k, m$$

---

## 2. Capacity Planning & Expansion Formulation

Introduce decision variable $y_{i,j,m} \ge 0$, representing the incremental capacity added to corridor $(i, j)$ on mode $m$.
Let $g_{i,j,m}$ denote the unit capital cost of capacity expansion (\$/ton capacity).

$$\min_{x, y} Z = \sum_{i,j,k,m} c_{i,j,m} \cdot x_{i,j,k,m} + \sum_{i,j,m} g_{i,j,m} \cdot y_{i,j,m}$$

Subject to:
$$\sum_{k \in K} x_{i,j,k,m} - y_{i,j,m} \le u_{i,j,m} \quad \forall i, j, m$$
$$\sum_{m \in M} x_{i,j,k,m} = d_{i,j,k} \quad \forall i, j, k$$
$$0 \le y_{i,j,m} \le \bar{Y}_{i,j,m}, \quad x_{i,j,k,m} \ge 0$$

### Economic Decision Criterion
From linear programming duality, if the shadow price $\pi_{i,j,m} > g_{i,j,m}$, expanding capacity on corridor $(i, j)$ for mode $m$ strictly reduces total system cost.

---

## 3. Disruption Resilience Formulation

Under an infrastructure disruption scenario $s \in \mathcal{S}$, available capacity is reduced by retention factor $\alpha_s \in [0, 1]$:
$$u_{i,j,m}^{(s)} = \alpha_s \cdot u_{i,j,m}$$

To prevent mathematical infeasibility during catastrophic closures, introduce non-negative unmet demand slack variables $q_{i,j,k} \ge 0$ with severe economic shortage penalty $P$:

$$\min_{x, q} Z = \sum_{i,j,k,m} c_{i,j,m} \cdot x_{i,j,k,m} + \sum_{i,j,k} P \cdot q_{i,j,k}$$

Subject to:
$$\sum_{m \in M} x_{i,j,k,m} + q_{i,j,k} = d_{i,j,k} \quad \forall i, j, k$$
$$\sum_{k \in K} x_{i,j,k,m} \le u_{i,j,m}^{(s)} \quad \forall i, j, m$$
$$x_{i,j,k,m} \ge 0, \quad q_{i,j,k} \ge 0$$

### Resilience Key Performance Indicators
1. **Resilience Service Ratio**:
   $$\text{RSR} = \frac{\sum_{i,j,k,m} x_{i,j,k,m}}{\sum_{i,j,k} d_{i,j,k}} \times 100\%$$
2. **Shortage Volume**:
   $$Q_{\text{unmet}} = \sum_{i,j,k} q_{i,j,k}$$
3. **Disruption Cost Delta**:
   $$\Delta Z = Z_{\text{disrupted}} - Z_{\text{baseline}}$$

---

## 4. Duality and Complementary Slackness
For canonical minimization $\min c^T x$ s.t. $A x \le b, x \ge 0$:
The Dual Problem is:
$$\max b^T y \quad \text{s.t.} \quad A^T y \le c, \quad y \le 0$$
**Strong Duality Theorem**: At optimality, $c^T x^* = b^T y^*$.
**Complementary Slackness Conditions**:
$$(b_i - A_i x^*) \cdot y_i^* = 0 \quad \forall i$$
$$(c_j - A_j^T y^*) \cdot x_j^* = 0 \quad \forall j$$
This confirms that whenever a corridor capacity constraint is strictly non-binding (has positive slack), its marginal shadow price is exactly zero.
