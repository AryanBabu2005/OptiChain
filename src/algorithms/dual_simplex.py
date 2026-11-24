"""
Dual Simplex Algorithm for OptiChain.
Starts from a dual-feasible, primal-infeasible basis and restores primal feasibility.
Enables rapid post-optimality reoptimization upon adding constraints or altering RHS vectors.
"""

from typing import Dict, Any, List, Optional
import numpy as np

class DualSimplexSolver:
    def __init__(self, tolerance: float = 1e-9, max_iterations: int = 500):
        self.tol = tolerance
        self.max_iter = max_iterations

    def solve_tableau(self, tableau: np.ndarray, basis: List[int],
                      maximize: bool = True) -> Dict[str, Any]:
        """
        Execute Dual Simplex on an existing tableau where row 0 is dual feasible (c_j >= 0)
        but one or more RHS b_i < 0.
        """
        tableau = tableau.copy()
        m = tableau.shape[0] - 1
        num_vars = tableau.shape[1] - 1

        status = "optimal"
        log = []

        for it in range(1, self.max_iter + 1):
            # Primal feasibility check: all b_i >= -tol
            rhs = tableau[1:, -1]
            min_rhs = np.min(rhs)

            if min_rhs >= -self.tol:
                status = "optimal"
                break

            # Leaving variable selection: most negative RHS
            pivot_row_idx = int(np.argmin(rhs))
            pivot_row = pivot_row_idx + 1

            # Entering variable selection: Dual Ratio Test
            # Consider columns where a_{pivot_row, j} < -tol
            row_coeffs = tableau[pivot_row, :-1]
            row0 = tableau[0, :-1]

            valid_ratios = []
            for j in range(num_vars):
                if row_coeffs[j] < -self.tol:
                    # ratio = row0[j] / |row_coeffs[j]|
                    ratio = abs(row0[j] / row_coeffs[j])
                    valid_ratios.append((ratio, j))

            if not valid_ratios:
                # No negative coefficients in pivot row => Primal is infeasible
                status = "infeasible"
                break

            valid_ratios.sort(key=lambda x: (x[0], x[1]))
            _, pivot_col = valid_ratios[0]
            pivot_elem = tableau[pivot_row, pivot_col]

            # Jordan elimination pivot
            tableau[pivot_row] /= pivot_elem
            for r in range(m + 1):
                if r != pivot_row:
                    tableau[r] -= tableau[r, pivot_col] * tableau[pivot_row]

            basis[pivot_row_idx] = pivot_col

            log.append({
                "iteration": it,
                "pivot_row": pivot_row,
                "pivot_col": pivot_col,
                "pivot_elem": float(pivot_elem)
            })

        final_obj = tableau[0, -1] if maximize else -tableau[0, -1]
        return {
            "status": status,
            "objective_value": round(float(final_obj), 6) if status == "optimal" else None,
            "final_tableau": tableau,
            "basis": basis,
            "iterations": len(log)
        }

    def solve(self, c: np.ndarray, A: np.ndarray, b: np.ndarray,
              maximize: bool = True) -> Dict[str, Any]:
        """
        Standard interface for Dual Simplex from formulation.
        A x <= b, x >= 0 (where b may have negative values, but c satisfies dual feasibility).
        """
        c = np.array(c, dtype=float).flatten()
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float).flatten()
        m, n = A.shape

        obj_factor = 1.0 if maximize else -1.0
        c_work = c * obj_factor

        tableau = np.zeros((m + 1, n + m + 1), dtype=float)
        tableau[0, :n] = -c_work
        tableau[1:, :n] = A
        tableau[1:, n:n + m] = np.eye(m)
        tableau[1:, -1] = b

        basis = [n + i for i in range(m)]

        # Check if already dual feasible (row 0 >= -tol)
        if np.min(tableau[0, :-1]) < -self.tol:
            # Not dual feasible; run regular simplex or two-phase
            from src.algorithms.simplex import SimplexSolver
            return SimplexSolver(tolerance=self.tol).solve(c, A, b, maximize=maximize)

        return self.solve_tableau(tableau, basis, maximize=maximize)
