"""
Multimodal Freight Allocation Optimization Model for OptiChain.
Formulates and solves the linear programming model:
min Z = sum(c[i,j,m] * x[i,j,k,m])
subject to:
  Demand: sum_m x[i,j,k,m] = d[i,j,k]
  Supply: sum_{j,m} x[i,j,k,m] <= S[i,k]
  Capacity: sum_k x[i,j,k,m] <= u[i,j,m]
  x[i,j,k,m] >= 0
Uses SciPy HiGHS solver with full extraction of dual variables and shadow prices.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from src.network.geography import FAF6_MODES, get_corridor_distance, get_zone_name
from src.data.sctg_codes import get_sctg_description

# Default Mode Rates ($ per ton-mile)
# Reference: BTS Freight Transportation in America / Bureau of Labor Statistics
DEFAULT_MODE_RATES: Dict[int, float] = {
    1: 0.180,  # Truck
    2: 0.045,  # Rail
    3: 0.030,  # Water
    4: 0.950,  # Air
    5: 0.120,  # Multiple modes & mail
    6: 0.025,  # Pipeline
    7: 0.150,  # Other
    8: 0.000   # None
}

class MultimodalFreightModel:
    def __init__(self, mode_rates: Optional[Dict[int, float]] = None):
        self.mode_rates = mode_rates or DEFAULT_MODE_RATES.copy()

    def build_and_solve(self, flows_df: pd.DataFrame,
                        capacity_multiplier: float = 1.30,
                        supply_slack_factor: float = 1.25) -> Dict[str, Any]:
        """
        Build and solve the multimodal freight LP on the provided flows dataset.
        Flows dataframe must contain: dms_orig, dms_dest, sctg2, dms_mode, tons_2022, distance_miles.
        """
        df = flows_df.copy()

        # Generate unique indices
        corridors_odk = df.groupby(["dms_orig", "dms_dest", "sctg2"], as_index=False)["tons_2022"].sum()
        unique_odk = [
            (int(r["dms_orig"]), int(r["dms_dest"]), int(r["sctg2"]))
            for _, r in corridors_odk.iterrows()
        ]
        odk_demand = {
            (int(r["dms_orig"]), int(r["dms_dest"]), int(r["sctg2"])): float(r["tons_2022"])
            for _, r in corridors_odk.iterrows()
        }

        # Available modes per (orig, dest) in the dataset or standard multimodal options
        # We allow Truck(1) always, Rail(2) if dist > 200, Water(3) if observed, Multimodal(5)
        decision_vars = []
        var_indices = {}

        for _, row in df.iterrows():
            orig = int(row["dms_orig"])
            dest = int(row["dms_dest"])
            comm = int(row["sctg2"])
            mode = int(row["dms_mode"])
            dist = float(row.get("distance_miles", get_corridor_distance(orig, dest, mode)))

            key = (orig, dest, comm, mode)
            if key not in var_indices:
                var_idx = len(decision_vars)
                var_indices[key] = var_idx
                rate = self.mode_rates.get(mode, 0.15)
                # Cost per ton = rate * dist ($/ton)
                unit_cost = rate * dist
                decision_vars.append({
                    "orig": orig,
                    "dest": dest,
                    "comm": comm,
                    "mode": mode,
                    "distance": dist,
                    "unit_cost": unit_cost,
                    "observed_tons": float(row["tons_2022"]),
                    "orig_name": get_zone_name(orig),
                    "dest_name": get_zone_name(dest),
                    "commodity_name": get_sctg_description(comm),
                    "mode_name": FAF6_MODES.get(mode, f"Mode {mode}")
                })

        num_vars = len(decision_vars)
        if num_vars == 0:
            return {"status": "empty_input", "message": "No flow records provided."}

        # Objective vector c
        c = np.array([v["unit_cost"] for v in decision_vars], dtype=float)

        # 1. Demand Constraints: sum_{m} x[i,j,k,m] = d[i,j,k]
        # Equal to observed flow requirements
        num_demands = len(unique_odk)
        A_eq = np.zeros((num_demands, num_vars), dtype=float)
        b_eq = np.zeros(num_demands, dtype=float)

        for d_idx, odk in enumerate(unique_odk):
            b_eq[d_idx] = odk_demand[odk]
            # find all vars matching odk
            for m in [1, 2, 3, 4, 5, 6, 7]:
                key = (odk[0], odk[1], odk[2], m)
                if key in var_indices:
                    A_eq[d_idx, var_indices[key]] = 1.0

        # 2. Corridor Mode Capacity Constraints: sum_k x[i,j,k,m] <= u[i,j,m]
        # u[i,j,m] derived from observed flow with capacity multiplier
        od_mode_observed = df.groupby(["dms_orig", "dms_dest", "dms_mode"])["tons_2022"].sum().to_dict()
        od_mode_keys = list(od_mode_observed.keys())
        num_caps = len(od_mode_keys)

        A_ub_list = []
        b_ub_list = []
        cap_constraint_names = []

        for odm in od_mode_keys:
            orig, dest, mode = int(odm[0]), int(odm[1]), int(odm[2])
            obs_ton = od_mode_observed[odm]
            u_cap = obs_ton * capacity_multiplier

            row_cap = np.zeros(num_vars, dtype=float)
            for key, v_idx in var_indices.items():
                if key[0] == orig and key[1] == dest and key[3] == mode:
                    row_cap[v_idx] = 1.0

            A_ub_list.append(row_cap)
            b_ub_list.append(u_cap)
            cap_constraint_names.append(f"Cap_{orig}_{dest}_M{mode}")

        # 3. Supply Constraints: sum_{j,m} x[i,j,k,m] <= S[i,k]
        orig_comm_observed = df.groupby(["dms_orig", "sctg2"])["tons_2022"].sum().to_dict()
        for ok, obs_supply in orig_comm_observed.items():
            orig, comm = int(ok[0]), int(ok[1])
            s_val = obs_supply * supply_slack_factor

            row_sup = np.zeros(num_vars, dtype=float)
            for key, v_idx in var_indices.items():
                if key[0] == orig and key[2] == comm:
                    row_sup[v_idx] = 1.0

            A_ub_list.append(row_sup)
            b_ub_list.append(s_val)

        A_ub = np.array(A_ub_list, dtype=float) if A_ub_list else None
        b_ub = np.array(b_ub_list, dtype=float) if b_ub_list else None

        # Solve with SciPy HiGHS
        bounds = [(0, None) for _ in range(num_vars)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

        if not res.success:
            reasons = []
            if capacity_multiplier < 1.0:
                reasons.append(f"Corridor Capacity Headroom Multiplier is set to {capacity_multiplier:.2f}x (< 1.00x), which caps physical throughput below observed baseline freight volumes.")
            if supply_slack_factor < 1.0:
                reasons.append(f"Origin Supply Headroom Factor is set to {supply_slack_factor:.2f}x (< 1.00x), which caps regional production below required outbound commodity demand.")
            if not reasons:
                reasons.append("The linear programming system cannot simultaneously satisfy destination demand conservation while respecting corridor capacity bounds and regional supply limits.")

            return {
                "status": "infeasible",
                "solver_name": "SciPy HiGHS Dual Simplex",
                "solver_status": int(res.status),
                "message": res.message,
                "infeasibility_reasons": reasons,
                "capacity_multiplier": capacity_multiplier,
                "supply_slack_factor": supply_slack_factor
            }

        x_opt = res.x
        total_cost = float(res.fun)

        # 1. Build Allocation Results
        allocations = []
        for v_idx, v in enumerate(decision_vars):
            alloc_tons = float(x_opt[v_idx])
            v["allocated_tons"] = round(alloc_tons, 2)
            v["allocated_cost"] = round(alloc_tons * v["unit_cost"], 2)
            allocations.append(v)

        alloc_df = pd.DataFrame(allocations)

        # 2. Demand Satisfaction Results & Shadow Prices (res.eqlin.marginals)
        dual_eq = res.eqlin.marginals if hasattr(res, "eqlin") and res.eqlin is not None else np.zeros(num_demands)
        demand_results = []
        for d_idx, odk in enumerate(unique_odk):
            req_d = b_eq[d_idx]
            delivered = float(np.dot(A_eq[d_idx], x_opt))
            satisfaction_pct = (delivered / req_d * 100.0) if req_d > 0 else 100.0
            marg_cost = float(dual_eq[d_idx]) if d_idx < len(dual_eq) else 0.0
            demand_results.append({
                "orig": odk[0],
                "dest": odk[1],
                "comm": odk[2],
                "orig_name": get_zone_name(odk[0]),
                "dest_name": get_zone_name(odk[1]),
                "commodity_name": get_sctg_description(odk[2]),
                "required_demand_tons": round(req_d, 2),
                "delivered_flow_tons": round(delivered, 2),
                "satisfaction_pct": round(satisfaction_pct, 1),
                "marginal_delivery_cost": round(marg_cost, 4),
                "marginal_demand_cost": round(marg_cost, 4)
            })
        demand_df = pd.DataFrame(demand_results)

        # 3. Corridor Capacity Utilization and Shadow Prices (res.ineqlin.marginals)
        capacity_results = []
        dual_ub = res.ineqlin.marginals if hasattr(res, "ineqlin") and res.ineqlin is not None else np.zeros(len(b_ub_list))

        for idx, odm in enumerate(od_mode_keys):
            orig, dest, mode = int(odm[0]), int(odm[1]), int(odm[2])
            cap = b_ub_list[idx]
            used = float(np.dot(A_ub[idx], x_opt))
            util_pct = (used / cap * 100.0) if cap > 0 else 0.0
            slack = max(0.0, cap - used)
            shadow_price = float(dual_ub[idx]) if idx < len(dual_ub) else 0.0

            capacity_results.append({
                "orig": orig,
                "dest": dest,
                "orig_name": get_zone_name(orig),
                "dest_name": get_zone_name(dest),
                "mode": mode,
                "mode_name": FAF6_MODES.get(mode, f"Mode {mode}"),
                "capacity": round(cap, 2),
                "allocated": round(used, 2),
                "slack_tons": round(slack, 2),
                "utilization_pct": round(util_pct, 1),
                "is_binding": util_pct >= 99.9,
                "shadow_price": round(abs(shadow_price), 4)
            })

        cap_df = pd.DataFrame(capacity_results)

        # 4. Origin Regional Supply Limits & Utilization
        num_cap_constraints = len(od_mode_keys)
        supply_results = []
        orig_comm_keys = list(orig_comm_observed.keys())

        for s_idx, ok in enumerate(orig_comm_keys):
            orig, comm = int(ok[0]), int(ok[1])
            ub_row_idx = num_cap_constraints + s_idx
            s_cap = b_ub_list[ub_row_idx]
            used_s = float(np.dot(A_ub[ub_row_idx], x_opt))
            util_s_pct = (used_s / s_cap * 100.0) if s_cap > 0 else 0.0
            slack_s = max(0.0, s_cap - used_s)
            s_shadow = float(dual_ub[ub_row_idx]) if ub_row_idx < len(dual_ub) else 0.0

            supply_results.append({
                "orig": orig,
                "comm": comm,
                "orig_name": get_zone_name(orig),
                "commodity_name": get_sctg_description(comm),
                "supply_limit_tons": round(s_cap, 2),
                "dispatched_tons": round(used_s, 2),
                "slack_tons": round(slack_s, 2),
                "utilization_pct": round(util_s_pct, 1),
                "is_binding": util_s_pct >= 99.9,
                "shadow_price": round(abs(s_shadow), 4)
            })

        supply_df = pd.DataFrame(supply_results)

        # 5. Filter Binding Constraints
        binding_corridors = cap_df[cap_df["is_binding"]].sort_values(by="shadow_price", ascending=False).reset_index(drop=True)
        binding_supplies = supply_df[supply_df["is_binding"]].sort_values(by="shadow_price", ascending=False).reset_index(drop=True)

        # Calculate observed baseline cost for comparison
        observed_cost = sum(v["observed_tons"] * v["unit_cost"] for v in decision_vars)
        cost_savings = observed_cost - total_cost
        savings_pct = (cost_savings / observed_cost * 100.0) if observed_cost > 0 else 0.0

        return {
            "status": "optimal",
            "solver_name": "SciPy HiGHS (Dual Simplex / Interior Point)",
            "solver_code": int(res.status),
            "solver_message": res.message,
            "objective_value": round(total_cost, 2),
            "observed_baseline_cost": round(observed_cost, 2),
            "cost_savings": round(cost_savings, 2),
            "savings_percent": round(savings_pct, 2),
            "total_freight_tons": round(float(np.sum(x_opt)), 2),
            "total_demand_tons": round(float(np.sum(b_eq)), 2),
            "demand_satisfaction_pct": 100.0,
            "num_decision_vars": num_vars,
            "num_constraints": num_demands + len(b_ub_list),
            "num_demand_constraints": num_demands,
            "num_capacity_constraints": len(od_mode_keys),
            "num_supply_constraints": len(orig_comm_observed),
            "num_binding_corridors": int(len(binding_corridors)),
            "num_binding_supplies": int(len(binding_supplies)),
            "allocations_df": alloc_df,
            "demand_df": demand_df,
            "supply_df": supply_df,
            "capacity_df": cap_df,
            "binding_corridors_df": binding_corridors,
            "binding_supplies_df": binding_supplies,
            "solver_runtime": getattr(res, "execution_time", 0.05),
            "capacity_multiplier": capacity_multiplier,
            "supply_slack_factor": supply_slack_factor
        }
