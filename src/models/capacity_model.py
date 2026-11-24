"""
Capacity Planning and Corridor Expansion Optimization Model for OptiChain.
Formulates LP with continuous capacity expansion decision variables y[i,j,m]:
min Z = sum(c[i,j,m] * x[i,j,k,m]) + sum(g[i,j,m] * y[i,j,m])
subject to:
  sum_k x[i,j,k,m] <= u[i,j,m] + y[i,j,m]
  Demand & supply balance constraints
  x >= 0, y >= 0
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from src.network.geography import FAF6_MODES, get_corridor_distance, get_zone_name

# Default Unit Capacity Expansion Cost ($/ton capacity)
DEFAULT_EXPANSION_COSTS: Dict[int, float] = {
    1: 25.0,  # Highway / lane expansion
    2: 15.0,  # Rail siding / double-tracking
    3: 10.0,  # Lock / channel dredging
    4: 150.0, # Airport cargo terminal expansion
    5: 20.0,  # Intermodal yard expansion
    6: 8.0,   # Pipeline pump station upgrade
    7: 20.0,
    8: 0.0
}

class CapacityPlanningModel:
    def __init__(self, expansion_costs: Optional[Dict[int, float]] = None):
        self.expansion_costs = expansion_costs or DEFAULT_EXPANSION_COSTS.copy()

    def plan_capacity(self, flows_df: pd.DataFrame,
                      base_capacity_factor: float = 1.05,
                      max_expansion_allowed: float = 1000.0) -> Dict[str, Any]:
        """
        Solve capacity expansion problem.
        """
        df = flows_df.copy()

        # Decision variables: flow vars x, expansion vars y
        flow_records = []
        var_indices = {}

        for _, row in df.iterrows():
            orig = int(row["dms_orig"])
            dest = int(row["dms_dest"])
            comm = int(row["sctg2"])
            mode = int(row["dms_mode"])
            dist = float(row.get("distance_miles", get_corridor_distance(orig, dest, mode)))

            key = (orig, dest, comm, mode)
            if key not in var_indices:
                var_indices[key] = len(flow_records)
                # Rate $0.18 for truck, $0.045 rail, etc.
                rate = 0.18 if mode == 1 else (0.045 if mode == 2 else 0.030)
                unit_cost = rate * dist
                flow_records.append({
                    "orig": orig,
                    "dest": dest,
                    "comm": comm,
                    "mode": mode,
                    "unit_cost": unit_cost,
                    "observed_tons": float(row["tons_2022"])
                })

        num_flow_vars = len(flow_records)

        # Corridors needing capacity
        od_mode_observed = df.groupby(["dms_orig", "dms_dest", "dms_mode"])["tons_2022"].sum().to_dict()
        od_mode_keys = list(od_mode_observed.keys())
        num_corridors = len(od_mode_keys)

        # Expansion variables y: index num_flow_vars + idx
        total_vars = num_flow_vars + num_corridors

        # Objective vector c
        c = np.zeros(total_vars, dtype=float)
        for i, rec in enumerate(flow_records):
            c[i] = rec["unit_cost"]

        for idx, odm in enumerate(od_mode_keys):
            mode = int(odm[2])
            g_cost = self.expansion_costs.get(mode, 20.0)
            c[num_flow_vars + idx] = g_cost

        # 1. Demand constraints: sum_m x[i,j,k,m] = d[i,j,k]
        unique_odk = df.groupby(["dms_orig", "dms_dest", "sctg2"])["tons_2022"].sum().to_dict()
        A_eq = np.zeros((len(unique_odk), total_vars), dtype=float)
        b_eq = np.zeros(len(unique_odk), dtype=float)

        for d_idx, (odk, dem_val) in enumerate(unique_odk.items()):
            b_eq[d_idx] = dem_val
            for m in [1, 2, 3, 4, 5]:
                key = (odk[0], odk[1], odk[2], m)
                if key in var_indices:
                    A_eq[d_idx, var_indices[key]] = 1.0

        # 2. Capacity constraints with expansion: sum_k x[i,j,k,m] - y[i,j,m] <= u[i,j,m]
        A_ub = np.zeros((num_corridors, total_vars), dtype=float)
        b_ub = np.zeros(num_corridors, dtype=float)

        for idx, odm in enumerate(od_mode_keys):
            orig, dest, mode = int(odm[0]), int(odm[1]), int(odm[2])
            u_base = od_mode_observed[odm] * base_capacity_factor
            b_ub[idx] = u_base

            # Flow coefficients
            for key, v_idx in var_indices.items():
                if key[0] == orig and key[1] == dest and key[3] == mode:
                    A_ub[idx, v_idx] = 1.0

            # Expansion coefficient: -1 * y
            A_ub[idx, num_flow_vars + idx] = -1.0

        bounds = [(0, None) for _ in range(num_flow_vars)] + [(0, max_expansion_allowed) for _ in range(num_corridors)]

        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        if not res.success:
            return {"status": "infeasible", "message": res.message}

        x_opt = res.x[:num_flow_vars]
        y_opt = res.x[num_flow_vars:]

        # Analysis of expansions
        expansion_summary = []
        for idx, odm in enumerate(od_mode_keys):
            orig, dest, mode = int(odm[0]), int(odm[1]), int(odm[2])
            base_cap = b_ub[idx]
            exp_cap = float(y_opt[idx])
            flow_alloc = float(np.dot(A_ub[idx, :num_flow_vars], x_opt))
            g_cost = c[num_flow_vars + idx]

            expansion_summary.append({
                "orig": orig,
                "dest": dest,
                "orig_name": get_zone_name(orig),
                "dest_name": get_zone_name(dest),
                "mode": mode,
                "mode_name": FAF6_MODES.get(mode, f"Mode {mode}"),
                "base_capacity": round(base_cap, 2),
                "expanded_capacity": round(exp_cap, 2),
                "total_capacity": round(base_cap + exp_cap, 2),
                "allocated_flow": round(flow_alloc, 2),
                "expansion_cost_per_ton": round(g_cost, 2),
                "total_expansion_expenditure": round(exp_cap * g_cost, 2),
                "expansion_recommended": exp_cap > 0.1
            })

        exp_df = pd.DataFrame(expansion_summary)
        recommended_df = exp_df[exp_df["expansion_recommended"]].sort_values(by="expanded_capacity", ascending=False)

        total_transport_cost = float(np.dot(c[:num_flow_vars], x_opt))
        total_expansion_cost = float(np.dot(c[num_flow_vars:], y_opt))

        return {
            "status": "optimal",
            "total_objective": round(float(res.fun), 2),
            "transportation_cost": round(total_transport_cost, 2),
            "capacity_expansion_cost": round(total_expansion_cost, 2),
            "num_expanded_corridors": len(recommended_df),
            "expansion_summary_df": exp_df,
            "recommended_expansions_df": recommended_df
        }
