"""
Primal Simplex Algorithm Implementation for OptiChain.
Supports maximization and minimization, standard form conversion,
iteration-by-iteration tableau logging, entering/leaving selection,
unboundedness detection, infeasibility detection, and degeneracy handling.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np

class SimplexSolver:
    def __init__(self, tolerance: float = 1e-9, max_iterations: int = 500):
        self.tol = tolerance
        self.max_iter = max_iterations

    def solve(self, c: np.ndarray, A: np.ndarray, b: np.ndarray,
              maximize: bool = True,
              constraint_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Solve standard LP problem using Simplex Tableau.
        max/min c^T x
        subject to A x (<=, ==, >=) b, x >= 0

        If constraint_types is None, assumes all '<='.
        For problems requiring artificial variables (>=, ==), delegates to TwoPhaseSimplex or Big-M.
        """
        c = np.array(c, dtype=float).flatten()
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float).flatten()

        m, n = A.shape
        if constraint_types is None:
            constraint_types = ["<="] * m

        # Ensure all b >= 0 (if b_i < 0, multiply row and flip constraint)
        for i in range(m):
            if b[i] < -self.tol:
                b[i] = -b[i]
                A[i] = -A[i]
                if constraint_types[i] == "<=":
                    constraint_types[i] = ">="
                elif constraint_types[i] == ">=":
                    constraint_types[i] = "<="

        # Check if artificial variables are needed (any '>=' or '==')
        needs_phase1 = any(ct in [">=", "=="] for ct in constraint_types)
        if needs_phase1:
            from src.algorithms.two_phase import TwoPhaseSimplex
            two_phase = TwoPhaseSimplex(tolerance=self.tol, max_iterations=self.max_iter)
            return two_phase.solve(c, A, b, maximize=maximize, constraint_types=constraint_types)

        # Standard form for all '<=' with slack variables
        # Maximize Z = c^T x  ==>  Z - c^T x = 0
        obj_factor = 1.0 if maximize else -1.0
        c_work = c * obj_factor

        # Tableau structure:
        # Row 0: [-c_work, 0 (slacks), 0 (RHS)]
        # Rows 1..m: [A, I, b]
        num_slacks = m
        total_vars = n + num_slacks

        tableau = np.zeros((m + 1, total_vars + 1), dtype=float)
        tableau[0, :n] = -c_work
        tableau[1:, :n] = A
        tableau[1:, n:n + num_slacks] = np.eye(m)
        tableau[1:, -1] = b

        basis = [n + i for i in range(m)]  # slack variables initially in basis

        iterations_log = []
        status = "optimal"

        # Record initial tableau
        iterations_log.append({
            "iteration": 0,
            "tableau": tableau.copy(),
            "basis": list(basis),
            "obj_value": -tableau[0, -1] if not maximize else tableau[0, -1],
            "pivot_row": None,
            "pivot_col": None
        })

        for it in range(1, self.max_iter + 1):
            # Optimality check: all reduced costs in row 0 must be >= -tol
            row0 = tableau[0, :-1]
            min_rc = np.min(row0)

            if min_rc >= -self.tol:
                status = "optimal"
                break

            # Entering variable selection (Dantzig's rule: most negative reduced cost)
            # Bland's rule: smallest index among negative candidates for tie-breaking
            pivot_col = int(np.argmin(row0))

            # Ratio test for leaving variable
            col_vals = tableau[1:, pivot_col]
            rhs_vals = tableau[1:, -1]

            valid_ratios = []
            for i in range(m):
                if col_vals[i] > self.tol:
                    ratio = rhs_vals[i] / col_vals[i]
                    valid_ratios.append((ratio, i))

            if not valid_ratios:
                # Unbounded problem: no positive entry in pivot column
                status = "unbounded"
                break

            # Minimum ratio test
            valid_ratios.sort(key=lambda x: (x[0], x[1]))  # Bland's tie break on index
            min_ratio, pivot_row_idx = valid_ratios[0]
            pivot_row = pivot_row_idx + 1  # 1-indexed in tableau

            pivot_elem = tableau[pivot_row, pivot_col]

            # Pivot Operation: Jordan elimination
            tableau[pivot_row] /= pivot_elem
            for r in range(m + 1):
                if r != pivot_row:
                    factor = tableau[r, pivot_col]
                    tableau[r] -= factor * tableau[pivot_row]

            # Update basis
            basis[pivot_row_idx] = pivot_col

            iterations_log.append({
                "iteration": it,
                "tableau": tableau.copy(),
                "basis": list(basis),
                "obj_value": -tableau[0, -1] if not maximize else tableau[0, -1],
                "pivot_row": pivot_row,
                "pivot_col": pivot_col,
                "pivot_element": float(pivot_elem),
                "ratio": float(min_ratio)
            })

            if it == self.max_iter:
                status = "iteration_limit_exceeded"

        # Extract solution
        x_sol = np.zeros(n, dtype=float)
        for i, b_var in enumerate(basis):
            if b_var < n:
                x_sol[b_var] = tableau[i + 1, -1]

        final_obj = tableau[0, -1] if maximize else -tableau[0, -1]

        # Check for alternate optima: non-basic variable with zero reduced cost
        alternate_optima = False
        for j in range(n):
            if j not in basis and abs(tableau[0, j]) < self.tol:
                alternate_optima = True
                break

        # Check for degeneracy: any basic variable with value 0
        degenerate = any(abs(tableau[i + 1, -1]) < self.tol for i in range(m))

        return {
            "status": status,
            "objective_value": round(float(final_obj), 6) if status == "optimal" else None,
            "x": np.round(x_sol, 6).tolist(),
            "basis": basis,
            "num_iterations": len(iterations_log) - 1,
            "iterations_log": iterations_log,
            "final_tableau": tableau,
            "alternate_optima": alternate_optima,
            "is_degenerate": degenerate
        }
