# OptiChain: Algorithm Notes & Syllabus Verification

This document provides mathematical notes, complexity analyses, and pseudocode for all algorithms implemented across University Syllabus Units I through IV.

---

## Unit I: Primal Simplex Algorithm
- **Role**: Solves standard LP problems $\max c^T x$ s.t. $A x \le b, x \ge 0$.
- **Complexity**: Worst-case exponential $O(2^n)$ (Klee-Minty cube), expected polynomial $O(m \cdot n)$ in practice.
- **Tableau Layout**:
  - Row 0: $[-c^T, 0_{\text{slack}}, 0_{\text{RHS}}]$.
  - Rows $1..m$: $[A, I_m, b]$.
- **Entering Variable**: Dantzig's rule selects $\min_j (r_j < 0)$. Bland's rule selects the lowest index $j$ among negative reduced costs to guarantee cycling prevention.
- **Leaving Variable**: Minimum Ratio Test:
  $$\theta^* = \min_{i: a_{i, \text{piv}} > 0} \left( \frac{b_i}{a_{i, \text{piv}}} \right)$$
- **Degeneracy Handling**: Flags basic variables where $b_i = 0$.

---

## Unit II: Artificial Variables and Duality
### Two-Phase Simplex
- **Phase I**: Adds artificial variables $a_i \ge 0$ for equality and $\ge$ constraints. Minimizes $W = \sum a_i$. If $\min W > 0$, the problem is proven **primal infeasible**.
- **Phase II**: Drops artificial columns, restores original objective function coefficients $c$, re-eliminates basic variables from row 0, and optimizes to final BFS.

### Big-M Method
- Assigns large penalty parameter $M$ in the objective function ($+M$ for minimization, $-M$ for maximization).
- Uses adaptive numerical scaling ($M = 100 \cdot \max(|c|) \cdot \max(|A|)$) and checks that no artificial variable remains positive in the final basis.

### Dual Simplex Algorithm
- Starts from a dual-feasible basis (all reduced costs optimal, $c_j \ge 0$), but primal-infeasible ($b_r < 0$).
- Selects pivot row by most negative RHS: $r = \text{argmin}_i (b_i)$.
- Selects pivot column by Dual Ratio Test: $\min_{j: a_{rj} < 0} \left| \frac{c_j}{a_{rj}} \right|$.

---

## Unit III: Transportation & MODI Optimization
### Initialization Methods
1. **Northwest Corner Method (NWCM)**:
   - Allocates from top-left cell $(0, 0)$ moving right or down based on exhausted supply or demand.
   - Fast $O(m + n)$, but ignores unit costs.
2. **Least Cost Method (LCM)**:
   - Greedily selects the lowest cost available matrix cell $C_{ij}$ and exhausts supply or demand.
   - Complexity: $O((m \cdot n) \log(m \cdot n))$.
3. **Vogel's Approximation Method (VAM)**:
   - Computes row and column penalties (difference between the two lowest costs in each row and column).
   - Allocates to the cell with the minimum cost in the row/column with the maximum penalty.
   - Complexity: $O((m + n) \cdot m \cdot n)$. Yields the lowest initial cost.

### MODI (Modified Distribution / $u-v$ Method)
- Evaluates optimality: Solves $u_i + v_j = C_{ij}$ for basic cells (setting $u_0 = 0$).
- Computes opportunity cost $\Delta_{ij} = C_{ij} - (u_i + v_j)$ for all non-basic cells.
- If all $\Delta_{ij} \ge 0$, current allocation is optimal.
- If $\Delta_{r, s} < 0$, finds closed stepping-stone loop, shifts flow $\theta = \min_{\text{negative corners}} X_{ij}$, and updates basis.

---

## Unit IV: Assignment & Game Theory
### Hungarian Algorithm (Kuhn-Munkres)
- Solves minimum-weight bipartite matching on $n \times n$ matrix in $O(n^3)$ time.
- Row reduction $\to$ Column reduction $\to$ Minimum line covering (König-Egerváry theorem) $\to$ Matrix augmentation.
- Handles rectangular matrices by padding with dummy rows/columns.
- Handles profit maximization via matrix inversion: $C'_{ij} = \max(C) - C_{ij}$.

### Two-Person Zero-Sum Game Theory
- Player 1 (Maximizer) vs Player 2 (Minimizer).
- **Saddle Point Test**: Maximin $\alpha^* = \max_i \min_j a_{ij}$; Minimax $\beta^* = \min_j \max_i a_{ij}$. If $\alpha^* = \beta^*$, pure strategy equilibrium exists.
- **$2 \times 2$ Mixed Strategy**: Analytical formulas for probabilities $p^*, q^*$ and game value $V$.
- **General $m \times n$ via LP**: Shifts payoffs positive, maximizes $V = 1 / \sum x_i$, solves via dual simplex.
