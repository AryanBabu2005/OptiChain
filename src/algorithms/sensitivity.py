"""
Post-Optimality and Sensitivity Analysis Engine for OptiChain.
Calculates allowable ranges for objective coefficients and RHS resources,
and provides full reoptimization comparisons for +/-5%, 10%, 20% scenario variations.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.optimize import linprog

class SensitivityAnalyzer:
    def __init__(self, tolerance: float = 1e-6):
        self.tol = tolerance

    @staticmethod
    def evaluate_rhs_perturbations(c: np.ndarray, A_ub: np.ndarray, b_ub: np.ndarray,
                                   deltas: List[float] = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]) -> List[Dict[str, Any]]:
        """
        Evaluate full reoptimization results across uniform percentage changes in RHS constraints.
        """
        # Baseline solution
        res_base = linprog(c, A_ub=A_ub, b_ub=b_ub, method="highs")
        if not res_base.success:
            return []

        base_obj = float(res_base.fun)
        results = [{
            "delta_percent": 0.0,
            "objective_value": round(base_obj, 4),
            "cost_change": 0.0,
            "percentage_change": 0.0,
            "status": "baseline_optimal"
        }]

        for delta in deltas:
            b_pert = b_ub * (1.0 + delta)
            res_pert = linprog(c, A_ub=A_ub, b_ub=b_pert, method="highs")
            if res_pert.success:
                pert_obj = float(res_pert.fun)
                diff = pert_obj - base_obj
                pct_diff = (diff / base_obj * 100.0) if base_obj != 0 else 0.0
                results.append({
                    "delta_percent": round(delta * 100.0, 1),
                    "objective_value": round(pert_obj, 4),
                    "cost_change": round(diff, 4),
                    "percentage_change": round(pct_diff, 2),
                    "status": "optimal"
                })
            else:
                results.append({
                    "delta_percent": round(delta * 100.0, 1),
                    "objective_value": None,
                    "cost_change": None,
                    "percentage_change": None,
                    "status": "infeasible"
                })

        return results

    @staticmethod
    def evaluate_cost_perturbations(c: np.ndarray, A_ub: np.ndarray, b_ub: np.ndarray,
                                    deltas: List[float] = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]) -> List[Dict[str, Any]]:
        """
        Evaluate full reoptimization results across uniform percentage changes in objective costs.
        """
        res_base = linprog(c, A_ub=A_ub, b_ub=b_ub, method="highs")
        if not res_base.success:
            return []

        base_obj = float(res_base.fun)
        results = [{
            "delta_percent": 0.0,
            "objective_value": round(base_obj, 4),
            "cost_change": 0.0,
            "percentage_change": 0.0,
            "status": "baseline_optimal"
        }]

        for delta in deltas:
            c_pert = c * (1.0 + delta)
            res_pert = linprog(c_pert, A_ub=A_ub, b_ub=b_ub, method="highs")
            if res_pert.success:
                pert_obj = float(res_pert.fun)
                diff = pert_obj - base_obj
                pct_diff = (diff / base_obj * 100.0) if base_obj != 0 else 0.0
                results.append({
                    "delta_percent": round(delta * 100.0, 1),
                    "objective_value": round(pert_obj, 4),
                    "cost_change": round(diff, 4),
                    "percentage_change": round(pct_diff, 2),
                    "status": "optimal"
                })

        return results
