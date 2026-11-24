"""
Freight Disruption Simulator and Resilience Engine for OptiChain.
Models network disruptions (closures, capacity drops, mode outages, cost surges),
evaluates unmet demand penalties, mode substitutions, and calculates the Network Resilience Service Ratio.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from src.network.geography import FAF6_MODES, get_corridor_distance, get_zone_name

class FreightDisruptionSimulator:
    def __init__(self, unmet_demand_penalty: float = 1000.0):
        # Penalty $ per ton of unmet demand
        self.penalty = unmet_demand_penalty

    def simulate_disruption(self, flows_df: pd.DataFrame,
                            disrupted_corridors: Optional[List[Tuple[int, int]]] = None,
                            disrupted_modes: Optional[List[int]] = None,
                            capacity_retention: float = 0.50,
                            cost_surge_factor: float = 1.0,
                            demand_surge_factor: float = 1.0) -> Dict[str, Any]:
        """
        Execute disruption resilience simulation.
        """
        df = flows_df.copy()
        disrupted_corridors = set(disrupted_corridors or [])
        disrupted_modes = set(disrupted_modes or [])

        # Step 1: Baseline solve without disruption
        from src.models.freight_model import MultimodalFreightModel
        base_model = MultimodalFreightModel()
        baseline_res = base_model.build_and_solve(df, capacity_multiplier=1.25)

        # Step 2: Formulate Disrupted Model with unmet demand slack q[i,j,k]
        # Variables: Flow vars x[i,j,k,m], Unmet demand vars q[i,j,k]
        unique_odk = df.groupby(["dms_orig", "dms_dest", "sctg2"])["tons_2022"].sum().to_dict()
        odk_list = list(unique_odk.keys())
        num_demands = len(odk_list)

        flow_vars = []
        var_indices = {}

        for _, row in df.iterrows():
            orig = int(row["dms_orig"])
            dest = int(row["dms_dest"])
            comm = int(row["sctg2"])
            mode = int(row["dms_mode"])
            dist = float(row.get("distance_miles", get_corridor_distance(orig, dest, mode)))

            key = (orig, dest, comm, mode)
            if key not in var_indices:
                var_indices[key] = len(flow_vars)
                rate = 0.18 if mode == 1 else (0.045 if mode == 2 else 0.030)
                # Apply cost surge if this corridor/mode is affected
                c_multiplier = cost_surge_factor if ((orig, dest) in disrupted_corridors or mode in disrupted_modes) else 1.0
                unit_cost = rate * dist * c_multiplier
                flow_vars.append({
                    "orig": orig,
                    "dest": dest,
                    "comm": comm,
                    "mode": mode,
                    "unit_cost": unit_cost,
                    "dist": dist
                })

        num_flow_vars = len(flow_vars)
        total_vars = num_flow_vars + num_demands  # flow vars + unmet demand vars

        # Objective vector c: flow costs + penalty for unmet demand
        c = np.zeros(total_vars, dtype=float)
        for i, v in enumerate(flow_vars):
            c[i] = v["unit_cost"]

        for d_idx in range(num_demands):
            c[num_flow_vars + d_idx] = self.penalty

        # 1. Demand constraints: sum_m x[i,j,k,m] + q[i,j,k] = d[i,j,k] * demand_surge
        A_eq = np.zeros((num_demands, total_vars), dtype=float)
        b_eq = np.zeros(num_demands, dtype=float)

        total_system_demand = 0.0
        for d_idx, odk in enumerate(odk_list):
            d_val = unique_odk[odk] * demand_surge_factor
            b_eq[d_idx] = d_val
            total_system_demand += d_val

            for m in [1, 2, 3, 4, 5]:
                key = (odk[0], odk[1], odk[2], m)
                if key in var_indices:
                    A_eq[d_idx, var_indices[key]] = 1.0

            # q variable coefficient = 1.0
            A_eq[d_idx, num_flow_vars + d_idx] = 1.0

        # 2. Capacity constraints: sum_k x[i,j,k,m] <= alpha * u[i,j,m]
        od_mode_observed = df.groupby(["dms_orig", "dms_dest", "dms_mode"])["tons_2022"].sum().to_dict()
        od_mode_keys = list(od_mode_observed.keys())

        A_ub = np.zeros((len(od_mode_keys), total_vars), dtype=float)
        b_ub = np.zeros(len(od_mode_keys), dtype=float)

        for idx, odm in enumerate(od_mode_keys):
            orig, dest, mode = int(odm[0]), int(odm[1]), int(odm[2])
            base_cap = od_mode_observed[odm] * 1.25

            # Determine retention alpha
            alpha = 1.0
            if (orig, dest) in disrupted_corridors or (dest, orig) in disrupted_corridors:
                alpha *= capacity_retention
            if mode in disrupted_modes:
                alpha *= capacity_retention

            b_ub[idx] = base_cap * alpha

            for key, v_idx in var_indices.items():
                if key[0] == orig and key[1] == dest and key[3] == mode:
                    A_ub[idx, v_idx] = 1.0

        bounds = [(0, None) for _ in range(total_vars)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        if not res.success:
            return {"status": "infeasible", "message": res.message}

        x_opt = res.x[:num_flow_vars]
        q_opt = res.x[num_flow_vars:]

        freight_served = float(np.sum(x_opt))
        unmet_freight = float(np.sum(q_opt))
        total_modeled_cost = float(np.dot(c[:num_flow_vars], x_opt))
        unmet_penalty_cost = float(np.dot(c[num_flow_vars:], q_opt))
        total_system_cost = total_modeled_cost + unmet_penalty_cost

        service_ratio = (freight_served / total_system_demand * 100.0) if total_system_demand > 0 else 100.0

        baseline_obj = baseline_res.get("objective_value", total_modeled_cost)
        cost_increase = total_system_cost - baseline_obj
        pct_cost_increase = (cost_increase / baseline_obj * 100.0) if baseline_obj > 0 else 0.0

        # Mode distribution in response
        mode_allocated = {}
        for i, v in enumerate(flow_vars):
            m = v["mode"]
            mode_allocated[m] = mode_allocated.get(m, 0.0) + float(x_opt[i])

        mode_shifts = []
        for m, alloc_ton in mode_allocated.items():
            mode_shifts.append({
                "mode": m,
                "mode_name": FAF6_MODES.get(m, f"Mode {m}"),
                "allocated_tons": round(alloc_ton, 2),
                "is_disrupted": m in disrupted_modes
            })

        return {
            "status": "optimal",
            "total_system_demand": round(total_system_demand, 2),
            "freight_served_tons": round(freight_served, 2),
            "unmet_demand_tons": round(unmet_freight, 2),
            "resilience_service_ratio": round(service_ratio, 2),
            "modeled_transportation_cost": round(total_modeled_cost, 2),
            "unmet_demand_penalty_cost": round(unmet_penalty_cost, 2),
            "total_objective_cost": round(total_system_cost, 2),
            "baseline_cost": round(baseline_obj, 2),
            "cost_increase": round(cost_increase, 2),
            "cost_increase_percent": round(pct_cost_increase, 2),
            "mode_shifts": mode_shifts,
            "disrupted_corridors_count": len(disrupted_corridors),
            "disrupted_modes_count": len(disrupted_modes)
        }
