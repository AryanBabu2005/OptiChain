"""
Independent Verification Engine for OptiChain.
Compares custom educational algorithm results against SciPy / HiGHS industry reference solver.
"""

from typing import Dict, Any, Tuple
import numpy as np
from scipy.optimize import linprog
from src.algorithms.simplex import SimplexSolver
from src.algorithms.two_phase import TwoPhaseSimplex

class SolverVerificationEngine:
    @staticmethod
    def verify_simplex_solution(c: np.ndarray, A: np.ndarray, b: np.ndarray,
                                maximize: bool = True, tolerance: float = 1e-4) -> Dict[str, Any]:
        """
        Verify custom Simplex against SciPy HiGHS.
        """
        c = np.array(c, dtype=float)
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float)

        # 1. Custom Simplex
        custom_solver = SimplexSolver()
        custom_res = custom_solver.solve(c, A, b, maximize=maximize)

        # 2. SciPy Reference
        c_scipy = -c if maximize else c
        scipy_res = linprog(c_scipy, A_ub=A, b_ub=b, method="highs")

        scipy_success = scipy_res.success
        scipy_obj = (-scipy_res.fun if maximize else scipy_res.fun) if scipy_success else None

        # Compare
        agrees = False
        discrepancy = None

        if custom_res["status"] == "optimal" and scipy_success:
            discrepancy = abs(custom_res["objective_value"] - scipy_obj)
            agrees = discrepancy <= tolerance
        elif custom_res["status"] == "infeasible" and not scipy_success:
            agrees = True
            discrepancy = 0.0
        elif custom_res["status"] == "unbounded" and scipy_res.status == 3:  # 3 = unbounded in scipy
            agrees = True
            discrepancy = 0.0

        return {
            "verified": agrees,
            "custom_status": custom_res["status"],
            "custom_objective": custom_res.get("objective_value"),
            "reference_status": "optimal" if scipy_success else scipy_res.message,
            "reference_objective": round(float(scipy_obj), 4) if scipy_obj is not None else None,
            "absolute_discrepancy": round(float(discrepancy), 6) if discrepancy is not None else None,
            "tolerance_used": tolerance
        }
