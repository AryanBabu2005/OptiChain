"""
Scenario Engine for OptiChain.
Performs parametric what-if scenario testing (+/-5%, 10%, 20%)
with full LP reoptimization and side-by-side comparative delta analytics.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from src.models.freight_model import MultimodalFreightModel

class ScenarioEngine:
    def __init__(self):
        self.model = MultimodalFreightModel()

    def run_scenario_comparison(self, flows_df: pd.DataFrame,
                                cost_delta_pct: float = 0.0,
                                demand_delta_pct: float = 0.0,
                                capacity_delta_pct: float = 0.0) -> Dict[str, Any]:
        """
        Run baseline vs scenario comparison with full reoptimization.
        """
        # Baseline
        base_res = self.model.build_and_solve(flows_df, capacity_multiplier=1.25)
        if base_res["status"] != "optimal":
            return {"status": "baseline_failed", "message": base_res.get("message", "")}

        # Scenario
        scen_df = flows_df.copy()
        if demand_delta_pct != 0.0:
            scen_df["tons_2022"] *= (1.0 + demand_delta_pct / 100.0)

        # Adjusted mode rates for cost delta
        scen_rates = {}
        for m, r in self.model.mode_rates.items():
            scen_rates[m] = r * (1.0 + cost_delta_pct / 100.0)

        scen_model = MultimodalFreightModel(mode_rates=scen_rates)
        scen_cap_mult = 1.25 * (1.0 + capacity_delta_pct / 100.0)
        scen_res = scen_model.build_and_solve(scen_df, capacity_multiplier=scen_cap_mult)

        if scen_res["status"] != "optimal":
            return {
                "status": "scenario_infeasible",
                "baseline_cost": base_res["objective_value"],
                "message": "Scenario resulted in infeasible network constraints."
            }

        base_obj = base_res["objective_value"]
        scen_obj = scen_res["objective_value"]
        cost_diff = scen_obj - base_obj
        pct_diff = (cost_diff / base_obj * 100.0) if base_obj > 0 else 0.0

        return {
            "status": "success",
            "baseline": {
                "objective_cost": base_obj,
                "total_tons": base_res["total_freight_tons"],
                "num_vars": base_res["num_decision_vars"]
            },
            "scenario": {
                "objective_cost": scen_obj,
                "total_tons": scen_res["total_freight_tons"],
                "cost_delta_pct": cost_delta_pct,
                "demand_delta_pct": demand_delta_pct,
                "capacity_delta_pct": capacity_delta_pct
            },
            "delta": {
                "cost_difference": round(cost_diff, 2),
                "percentage_cost_change": round(pct_diff, 2)
            }
        }
