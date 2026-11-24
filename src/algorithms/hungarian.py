"""
Hungarian Algorithm (Kuhn-Munkres) for Assignment Problems in OptiChain.
Finds optimal 1-to-1 matching for cost minimization or profit maximization.
Supports rectangular matrices (dummy row/column additions) and provides verification.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.optimize import linear_sum_assignment

class HungarianSolver:
    @staticmethod
    def solve(cost_matrix: np.ndarray, maximize: bool = False) -> Dict[str, Any]:
        """
        Solve assignment problem using the Hungarian algorithm.
        Supports rectangular matrices by padding with dummy assignments.
        """
        C_orig = np.array(cost_matrix, dtype=float).copy()
        m, n = C_orig.shape

        # Handle profit maximization by transformation
        if maximize:
            max_val = np.max(C_orig)
            C_work = max_val - C_orig
        else:
            C_work = C_orig.copy()

        # Handle rectangular matrix by padding to square max(m, n) x max(m, n)
        dim = max(m, n)
        C_padded = np.zeros((dim, dim), dtype=float)
        C_padded[:m, :n] = C_work

        # If dummy rows/columns are added, dummy cost is set high or 0 depending on maximization
        if dim > m:
            # Added dummy workers/origins
            C_padded[m:, :] = 0.0
        if dim > n:
            # Added dummy jobs/destinations
            C_padded[:, n:] = 0.0

        # Execute Hungarian assignment via linear_sum_assignment
        row_ind, col_ind = linear_sum_assignment(C_padded)

        # Filter out dummy assignments
        assignments = []
        total_obj = 0.0

        for r, c in zip(row_ind, col_ind):
            is_dummy = (r >= m) or (c >= n)
            real_cost = float(C_orig[r, c]) if not is_dummy else 0.0
            if not is_dummy:
                total_obj += real_cost
                assignments.append({
                    "row": int(r),
                    "col": int(c),
                    "cost": round(real_cost, 4),
                    "is_dummy": False
                })
            else:
                assignments.append({
                    "row": int(r),
                    "col": int(c),
                    "cost": 0.0,
                    "is_dummy": True
                })

        # Construct assignment matrix
        assignment_matrix = np.zeros((m, n), dtype=int)
        for a in assignments:
            if not a["is_dummy"]:
                assignment_matrix[a["row"], a["col"]] = 1

        return {
            "status": "optimal",
            "objective_value": round(float(total_obj), 4),
            "maximize": maximize,
            "assignments": assignments,
            "assignment_matrix": assignment_matrix,
            "original_shape": (m, n),
            "padded_shape": (dim, dim),
            "num_dummy_assigned": sum(1 for a in assignments if a["is_dummy"])
        }

    @staticmethod
    def brute_force_verify(cost_matrix: np.ndarray, maximize: bool = False) -> Dict[str, Any]:
        """
        Brute force enumeration of all permutations for small matrices (n <= 8) to verify.
        """
        import itertools
        C = np.array(cost_matrix, dtype=float)
        m, n = C.shape
        if m != n or m > 8:
            return {"verified": False, "message": "Brute force only supported for square matrices of size <= 8"}

        best_cost = -float("inf") if maximize else float("inf")
        best_perm = None

        for perm in itertools.permutations(range(n)):
            cost = sum(C[i, perm[i]] for i in range(n))
            if maximize:
                if cost > best_cost:
                    best_cost = cost
                    best_perm = perm
            else:
                if cost < best_cost:
                    best_cost = cost
                    best_perm = perm

        return {
            "verified": True,
            "best_cost": round(float(best_cost), 4),
            "permutation": list(best_perm)
        }
