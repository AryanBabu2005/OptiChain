"""
Big-M Simplex Algorithm for OptiChain.
Applies penalty M to artificial variables in the objective function.
Includes numerical scaling and rigorous post-optimality feasibility check.
"""

from typing import Dict, Any, List, Optional
import numpy as np

class BigMSimplex:
    def __init__(self, tolerance: float = 1e-7, max_iterations: int = 500):
        self.tol = tolerance
        self.max_iter = max_iterations

    def solve(self, c: np.ndarray, A: np.ndarray, b: np.ndarray,
              maximize: bool = True,
              constraint_types: Optional[List[str]] = None,
              m_penalty: Optional[float] = None) -> Dict[str, Any]:
        """
        Solve linear program using the Big-M method.
        """
        c = np.array(c, dtype=float).flatten()
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float).flatten()
        m, n = A.shape

        if constraint_types is None:
            constraint_types = ["<="] * m

        # Ensure b >= 0
        for i in range(m):
            if b[i] < -self.tol:
                b[i] = -b[i]
                A[i] = -A[i]
                if constraint_types[i] == "<=":
                    constraint_types[i] = ">="
                elif constraint_types[i] == ">=":
                    constraint_types[i] = "<="

        # Adaptive M penalty calculation to maintain numerical stability
        if m_penalty is None:
            max_c = np.max(np.abs(c)) if len(c) > 0 and np.max(np.abs(c)) > 0 else 1.0
            max_A = np.max(np.abs(A)) if np.max(np.abs(A)) > 0 else 1.0
            M = max(1000.0, 100.0 * max_c * max_A)
        else:
            M = float(m_penalty)

        n_slack = sum(1 for ct in constraint_types if ct == "<=")
        n_surplus = sum(1 for ct in constraint_types if ct == ">=")
        n_art = sum(1 for ct in constraint_types if ct in [">=", "=="])

        total_vars = n + n_slack + n_surplus + n_art
        tableau = np.zeros((m + 1, total_vars + 1), dtype=float)
        tableau[1:, :n] = A
        tableau[1:, -1] = b

        curr_slack = n
        curr_surplus = n + n_slack
        curr_art = n + n_slack + n_surplus

        basis = [0] * m
        art_indices = []

        for i, ct in enumerate(constraint_types):
            if ct == "<=":
                tableau[i + 1, curr_slack] = 1.0
                basis[i] = curr_slack
                curr_slack += 1
            elif ct == ">=":
                tableau[i + 1, curr_surplus] = -1.0
                curr_surplus += 1
                tableau[i + 1, curr_art] = 1.0
                basis[i] = curr_art
                art_indices.append(curr_art)
                curr_art += 1
            elif ct == "==":
                tableau[i + 1, curr_art] = 1.0
                basis[i] = curr_art
                art_indices.append(curr_art)
                curr_art += 1

        # Objective row setup
        # For max: Z - c^T x + M * sum(art) = 0
        # For min: Z + c^T x + M * sum(art) = 0
        obj_factor = 1.0 if maximize else -1.0
        c_work = c * obj_factor

        tableau[0, :n] = -c_work
        # Artificial penalty in maximization is -M, in row 0 equation it becomes +M
        for art_col in art_indices:
            tableau[0, art_col] = M

        # Eliminate artificial basic variables from row 0
        for i in range(m):
            if basis[i] in art_indices:
                tableau[0] -= M * tableau[i + 1]

        # Simplex iterations
        status = "optimal"
        for it in range(1, self.max_iter + 1):
            row0 = tableau[0, :-1]
            min_rc = np.min(row0)
            if min_rc >= -self.tol:
                break

            pivot_col = int(np.argmin(row0))

            col_vals = tableau[1:, pivot_col]
            rhs_vals = tableau[1:, -1]

            valid_ratios = []
            for i in range(m):
                if col_vals[i] > self.tol:
                    valid_ratios.append((rhs_vals[i] / col_vals[i], i))

            if not valid_ratios:
                status = "unbounded"
                break

            valid_ratios.sort(key=lambda x: (x[0], x[1]))
            _, pivot_row_idx = valid_ratios[0]
            pivot_row = pivot_row_idx + 1
            pivot_elem = tableau[pivot_row, pivot_col]

            tableau[pivot_row] /= pivot_elem
            for r in range(m + 1):
                if r != pivot_row:
                    tableau[r] -= tableau[r, pivot_col] * tableau[pivot_row]

            basis[pivot_row_idx] = pivot_col

        # Check if artificial variables remain in the basis with positive value
        for i, b_var in enumerate(basis):
            if b_var in art_indices:
                val = tableau[i + 1, -1]
                if val > self.tol:
                    return {
                        "status": "infeasible",
                        "objective_value": None,
                        "x": None,
                        "message": f"Infeasible: Artificial variable {b_var} remains positive ({val:.4f}) in basis."
                    }

        # Extract solution
        x_sol = np.zeros(n, dtype=float)
        for i, b_var in enumerate(basis):
            if b_var < n:
                x_sol[b_var] = tableau[i + 1, -1]

        final_obj = tableau[0, -1] if maximize else -tableau[0, -1]

        return {
            "status": status,
            "objective_value": round(float(final_obj), 6) if status == "optimal" else None,
            "x": np.round(x_sol, 6).tolist(),
            "basis": basis,
            "m_value_used": M
        }
