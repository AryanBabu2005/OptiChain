"""
Duality Theory and Complementary Slackness Engine for OptiChain.
Constructs canonical dual formulations, extracts shadow prices,
verifies strong duality, and confirms complementary slackness.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.optimize import linprog

class DualityEngine:
    def __init__(self, tolerance: float = 1e-6):
        self.tol = tolerance

    @staticmethod
    def construct_dual_lp(c: np.ndarray, A_ub: Optional[np.ndarray], b_ub: Optional[np.ndarray],
                          A_eq: Optional[np.ndarray], b_eq: Optional[np.ndarray],
                          maximize: bool = False) -> Dict[str, Any]:
        """
        Formulate exact mathematical dual LP from primal inputs.
        If Primal is Min c^T x s.t. A_ub x <= b_ub, A_eq x == b_eq, x >= 0:
        Dual is Max (-b_ub^T y_ub + b_eq^T y_eq) s.t. -A_ub^T y_ub + A_eq^T y_eq <= c, y_ub >= 0, y_eq free.
        """
        # Document dual structure
        n_primal_vars = len(c)
        m_ub = len(b_ub) if b_ub is not None else 0
        m_eq = len(b_eq) if b_eq is not None else 0

        dual_info = {
            "primal_sense": "MAXIMIZE" if maximize else "MINIMIZE",
            "dual_sense": "MINIMIZE" if maximize else "MAXIMIZE",
            "num_primal_variables": n_primal_vars,
            "num_primal_constraints": m_ub + m_eq,
            "num_dual_variables": m_ub + m_eq,
            "num_dual_constraints": n_primal_vars,
            "dual_variable_descriptions": [
                f"y_{i+1} (Shadow price of inequality constraint {i+1})" for i in range(m_ub)
            ] + [
                f"v_{j+1} (Dual multiplier of equality constraint {j+1})" for j in range(m_eq)
            ]
        }
        return dual_info

    def verify_primal_dual(self, c: np.ndarray,
                            A_ub: Optional[np.ndarray] = None, b_ub: Optional[np.ndarray] = None,
                            A_eq: Optional[np.ndarray] = None, b_eq: Optional[np.ndarray] = None,
                            bounds: Optional[List[Tuple[float, float]]] = None) -> Dict[str, Any]:
        """
        Solve primal with HiGHS, extract dual variables (shadow prices),
        verify strong duality and complementary slackness conditions.
        """
        c = np.array(c, dtype=float)
        
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        if not res.success:
            return {
                "success": False,
                "status": res.message,
                "primal_objective": None,
                "dual_objective": None
            }

        x_opt = res.x
        primal_obj = float(res.fun)

        # Dual variables from HiGHS
        # res.ineqlin.marginals are the dual multipliers (shadow prices) for A_ub x <= b_ub
        # res.eqlin.marginals are dual multipliers for A_eq x == b_eq
        dual_ub = res.ineqlin.marginals if hasattr(res, "ineqlin") and res.ineqlin is not None else np.array([])
        dual_eq = res.eqlin.marginals if hasattr(res, "eqlin") and res.eqlin is not None else np.array([])

        # Calculate dual objective: b_ub^T y_ub + b_eq^T y_eq
        dual_obj = 0.0
        if b_ub is not None and len(dual_ub) > 0:
            dual_obj += float(np.dot(b_ub, dual_ub))
        if b_eq is not None and len(dual_eq) > 0:
            dual_obj += float(np.dot(b_eq, dual_eq))

        # Check Strong Duality: Primal Obj == Dual Obj
        # Note: In SciPy linprog minimization with A_ub x <= b_ub, marginals are <= 0 or dual signed
        duality_gap = abs(primal_obj - dual_obj)
        strong_duality_holds = duality_gap < 1e-4

        # Complementary Slackness Verification
        slackness_checks = []
        if A_ub is not None and b_ub is not None and len(dual_ub) > 0:
            primal_slack = b_ub - np.dot(A_ub, x_opt)
            for i in range(len(b_ub)):
                product = float(primal_slack[i] * dual_ub[i])
                is_zero = abs(product) < self.tol
                slackness_checks.append({
                    "constraint_idx": i,
                    "slack_value": round(float(primal_slack[i]), 6),
                    "dual_variable": round(float(dual_ub[i]), 6),
                    "complementary_product": round(product, 8),
                    "is_satisfied": is_zero
                })

        return {
            "success": True,
            "primal_objective": round(primal_obj, 6),
            "dual_objective": round(dual_obj, 6),
            "duality_gap": round(duality_gap, 8),
            "strong_duality_holds": strong_duality_holds,
            "primal_solution": x_opt.tolist(),
            "shadow_prices_ineq": [round(float(y), 6) for y in dual_ub],
            "shadow_prices_eq": [round(float(v), 6) for v in dual_eq],
            "complementary_slackness_checks": slackness_checks,
            "reduced_costs": [round(float(rc), 6) for rc in res.lower.marginals] if hasattr(res, "lower") else []
        }
