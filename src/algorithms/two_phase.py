"""
Two-Phase Simplex Algorithm for OptiChain.
Handles mixed constraints (<=, ==, >=) using Phase I to find an initial Basic Feasible Solution (BFS)
and Phase II to optimize the original objective function.
Explicitly detects and flags primal infeasibility.
"""

from typing import Dict, Any, List, Optional
import numpy as np

class TwoPhaseSimplex:
    def __init__(self, tolerance: float = 1e-9, max_iterations: int = 500):
        self.tol = tolerance
        self.max_iter = max_iterations

    def solve(self, c: np.ndarray, A: np.ndarray, b: np.ndarray,
              maximize: bool = True,
              constraint_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Solve linear program using Two-Phase Simplex.
        """
        c = np.array(c, dtype=float).flatten()
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float).flatten()
        m, n = A.shape

        if constraint_types is None:
            constraint_types = ["<="] * m

        # Ensure all b_i >= 0
        for i in range(m):
            if b[i] < -self.tol:
                b[i] = -b[i]
                A[i] = -A[i]
                if constraint_types[i] == "<=":
                    constraint_types[i] = ">="
                elif constraint_types[i] == ">=":
                    constraint_types[i] = "<="

        # Identify variable types:
        # For each constraint i:
        # '<=': +1 slack variable
        # '>=': -1 surplus variable, +1 artificial variable
        # '==': +1 artificial variable
        slack_cols = []
        surplus_cols = []
        artificial_cols = []

        # Count variables
        n_slack = sum(1 for ct in constraint_types if ct == "<=")
        n_surplus = sum(1 for ct in constraint_types if ct == ">=")
        n_art = sum(1 for ct in constraint_types if ct in [">=", "=="])

        total_vars_p1 = n + n_slack + n_surplus + n_art
        tableau_p1 = np.zeros((m + 1, total_vars_p1 + 1), dtype=float)
        tableau_p1[1:, :n] = A
        tableau_p1[1:, -1] = b

        curr_slack = n
        curr_surplus = n + n_slack
        curr_art = n + n_slack + n_surplus

        basis = [0] * m
        art_indices = []

        for i, ct in enumerate(constraint_types):
            if ct == "<=":
                tableau_p1[i + 1, curr_slack] = 1.0
                basis[i] = curr_slack
                curr_slack += 1
            elif ct == ">=":
                tableau_p1[i + 1, curr_surplus] = -1.0
                curr_surplus += 1
                tableau_p1[i + 1, curr_art] = 1.0
                basis[i] = curr_art
                art_indices.append(curr_art)
                curr_art += 1
            elif ct == "==":
                tableau_p1[i + 1, curr_art] = 1.0
                basis[i] = curr_art
                art_indices.append(curr_art)
                curr_art += 1

        # Phase I Objective: Minimize W = sum(artificial) => Maximize -W = -sum(artificial)
        # In tableau, row 0 has +1 for artificials, but we must express in terms of non-basic vars
        # Z_art = -sum(art) => row 0 is sum of constraint rows with artificials
        for art_col in art_indices:
            tableau_p1[0, art_col] = 1.0

        # Eliminate artificials from row 0: subtract each row where art is basic
        for i in range(m):
            if basis[i] in art_indices:
                tableau_p1[0] -= tableau_p1[i + 1]

        # Solve Phase I
        p1_log = []
        p1_status = "optimal"

        for it in range(1, self.max_iter + 1):
            row0 = tableau_p1[0, :-1]
            min_rc = np.min(row0)
            if min_rc >= -self.tol:
                break

            pivot_col = int(np.argmin(row0))

            # Ratio test
            col_vals = tableau_p1[1:, pivot_col]
            rhs_vals = tableau_p1[1:, -1]

            valid_ratios = []
            for i in range(m):
                if col_vals[i] > self.tol:
                    valid_ratios.append((rhs_vals[i] / col_vals[i], i))

            if not valid_ratios:
                p1_status = "unbounded"
                break

            valid_ratios.sort(key=lambda x: (x[0], x[1]))
            _, pivot_row_idx = valid_ratios[0]
            pivot_row = pivot_row_idx + 1
            pivot_elem = tableau_p1[pivot_row, pivot_col]

            tableau_p1[pivot_row] /= pivot_elem
            for r in range(m + 1):
                if r != pivot_row:
                    tableau_p1[r] -= tableau_p1[r, pivot_col] * tableau_p1[pivot_row]

            basis[pivot_row_idx] = pivot_col

        # Check Phase I Result
        w_val = -tableau_p1[0, -1]  # optimal W
        if abs(w_val) > self.tol and w_val > self.tol:
            # Non-zero sum of artificials means infeasible!
            return {
                "status": "infeasible",
                "phase": 1,
                "objective_value": None,
                "x": None,
                "basis": basis,
                "message": f"Problem is primal infeasible (Phase I minimum artificial sum = {w_val:.6f} > 0)."
            }

        # Any artificial remaining in basis with value 0 must be driven out or kept degenerate
        # Phase II: Remove artificial columns
        non_art_cols = [j for j in range(total_vars_p1) if j not in art_indices]
        tableau_p2 = np.zeros((m + 1, len(non_art_cols) + 1), dtype=float)

        col_map = {old_j: new_j for new_j, old_j in enumerate(non_art_cols)}

        for r in range(1, m + 1):
            for old_j in non_art_cols:
                tableau_p2[r, col_map[old_j]] = tableau_p1[r, old_j]
            tableau_p2[r, -1] = tableau_p1[r, -1]

        # Update basis indices
        basis_p2 = []
        for b_var in basis:
            if b_var in col_map:
                basis_p2.append(col_map[b_var])
            else:
                # Artificial remained at 0 in basis; replace with available non-basic column
                basis_p2.append(0)

        # Set Phase II original objective function
        obj_factor = 1.0 if maximize else -1.0
        c_work = c * obj_factor

        for j in range(n):
            tableau_p2[0, col_map[j]] = -c_work[j]

        # Eliminate basic variables from Phase II row 0
        for i in range(m):
            b_var = basis_p2[i]
            coeff = tableau_p2[0, b_var]
            if abs(coeff) > self.tol:
                tableau_p2[0] -= coeff * tableau_p2[i + 1]

        # Solve Phase II
        p2_status = "optimal"
        for it in range(1, self.max_iter + 1):
            row0 = tableau_p2[0, :-1]
            min_rc = np.min(row0)
            if min_rc >= -self.tol:
                break

            pivot_col = int(np.argmin(row0))

            col_vals = tableau_p2[1:, pivot_col]
            rhs_vals = tableau_p2[1:, -1]

            valid_ratios = []
            for i in range(m):
                if col_vals[i] > self.tol:
                    valid_ratios.append((rhs_vals[i] / col_vals[i], i))

            if not valid_ratios:
                p2_status = "unbounded"
                break

            valid_ratios.sort(key=lambda x: (x[0], x[1]))
            _, pivot_row_idx = valid_ratios[0]
            pivot_row = pivot_row_idx + 1
            pivot_elem = tableau_p2[pivot_row, pivot_col]

            tableau_p2[pivot_row] /= pivot_elem
            for r in range(m + 1):
                if r != pivot_row:
                    tableau_p2[r] -= tableau_p2[r, pivot_col] * tableau_p2[pivot_row]

            basis_p2[pivot_row_idx] = pivot_col

        # Extract solution
        x_sol = np.zeros(n, dtype=float)
        for i, b_var in enumerate(basis_p2):
            for orig_j in range(n):
                if col_map[orig_j] == b_var:
                    x_sol[orig_j] = tableau_p2[i + 1, -1]

        final_obj = tableau_p2[0, -1] if maximize else -tableau_p2[0, -1]

        return {
            "status": p2_status,
            "objective_value": round(float(final_obj), 6) if p2_status == "optimal" else None,
            "x": np.round(x_sol, 6).tolist(),
            "basis": basis_p2,
            "final_tableau": tableau_p2
        }
