"""
Decarbonization, Scope 3 Emissions, and Green Logistics Engine for OptiChain.
Calculates modal greenhouse gas (GHG) footprints and generates bi-objective
Pareto optimal trade-offs between logistics cost ($) and carbon emissions (t CO2e).
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from src.network.geography import FAF6_MODES, get_corridor_distance, get_zone_name

# EPA SmartWay and GLEC (Global Logistics Emissions Council) Framework Benchmarks
# Unit: grams CO2 equivalent per ton-mile (g CO2e / ton-mile)
EMISSION_FACTORS_G_PER_TON_MILE: Dict[int, float] = {
    1: 161.8,  # Highway Truck (Class 8 Diesel Tractor-Trailer)
    2: 22.0,   # Class I Freight Rail (Diesel-Electric Locomotive, 7.3x lower than truck)
    3: 19.3,   # Inland Waterway Barge / Coastal Vessel (8.4x lower than truck)
    4: 1520.0, # Dedicated Air Cargo Freighter
    5: 65.0,   # Intermodal Containerized (Rail-Highway blend)
    6: 15.0,   # Crude / Products Pipeline
    7: 120.0,  # Other & Unknown
    8: 0.0     # None
}

class GreenLogisticsEngine:
    def __init__(self, emission_factors: Optional[Dict[int, float]] = None):
        self.factors = emission_factors or EMISSION_FACTORS_G_PER_TON_MILE.copy()

    def compute_flow_emissions(self, tons: float, distance_miles: float, mode: int) -> float:
        """
        Compute metric tons of CO2e for a given shipment flow.
        Tons * Distance (miles) * Factor (g/ton-mile) / 1,000,000 (g/metric ton).
        """
        factor = self.factors.get(mode, 120.0)
        ton_miles = tons * distance_miles
        co2_metric_tons = (ton_miles * factor) / 1_000_000.0
        return round(co2_metric_tons, 2)

    def evaluate_network_emissions(self, flows_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate full network carbon emissions breakdown by mode and commodity.
        """
        df = flows_df.copy()
        df["co2e_metric_tons"] = df.apply(
            lambda r: self.compute_flow_emissions(
                float(r["tons_2022"]),
                float(r.get("distance_miles", 200.0)),
                int(r["dms_mode"])
            ),
            axis=1
        )

        total_co2e = float(df["co2e_metric_tons"].sum())
        total_tons = float(df["tons_2022"].sum())
        total_ton_miles = float(df["thousand_ton_miles"].sum() * 1000.0) if "thousand_ton_miles" in df.columns else total_tons * 400.0

        # Mode emissions breakdown
        mode_agg = df.groupby("dms_mode", as_index=False).agg({
            "tons_2022": "sum",
            "co2e_metric_tons": "sum"
        })
        mode_agg["mode_name"] = mode_agg["dms_mode"].map(lambda m: FAF6_MODES.get(m, f"Mode {m}"))
        mode_agg["share_of_emissions_pct"] = (mode_agg["co2e_metric_tons"] / total_co2e * 100.0) if total_co2e > 0 else 0.0
        mode_agg["intensity_kg_per_ton"] = np.where(
            mode_agg["tons_2022"] > 0,
            (mode_agg["co2e_metric_tons"] * 1000.0) / mode_agg["tons_2022"],
            0.0
        )

        return {
            "total_co2e_metric_tons": round(total_co2e, 1),
            "total_co2e_megatons": round(total_co2e / 1_000_000.0, 3),
            "average_network_intensity_g_per_tm": round((total_co2e * 1_000_000.0) / total_ton_miles, 1) if total_ton_miles > 0 else 0.0,
            "mode_breakdown_df": mode_agg.sort_values(by="co2e_metric_tons", ascending=False).reset_index(drop=True)
        }

    def generate_pareto_frontier(self, flows_df: pd.DataFrame, num_points: int = 7) -> List[Dict[str, Any]]:
        """
        Generate Bi-Objective Pareto Frontier: Logistics Cost ($) vs Carbon Emissions (t CO2e).
        Uses weighted-sum scalarization:
        min Z = (1 - alpha) * Normalized_Cost + alpha * Normalized_Emissions
        where alpha ranges from 0.0 (Pure Cost) to 1.0 (Pure Green).
        """
        df = flows_df.copy()

        # Build decision variable set
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
                rate = 0.180 if mode == 1 else (0.045 if mode == 2 else 0.030)
                unit_cost = rate * dist
                # Unit CO2e in metric tons per thousand tons = dist * factor / 1000
                factor = self.factors.get(mode, 120.0)
                unit_emissions = (dist * factor) / 1000.0

                flow_records.append({
                    "orig": orig,
                    "dest": dest,
                    "comm": comm,
                    "mode": mode,
                    "unit_cost": unit_cost,
                    "unit_emissions": unit_emissions,
                    "dist": dist
                })

        num_vars = len(flow_records)
        if num_vars == 0:
            return []

        cost_vec = np.array([r["unit_cost"] for r in flow_records])
        emiss_vec = np.array([r["unit_emissions"] for r in flow_records])

        # Normalize objectives for balanced weighting
        max_c = np.max(cost_vec) if np.max(cost_vec) > 0 else 1.0
        max_e = np.max(emiss_vec) if np.max(emiss_vec) > 0 else 1.0

        # Constraints
        unique_odk = df.groupby(["dms_orig", "dms_dest", "sctg2"])["tons_2022"].sum().to_dict()
        num_demands = len(unique_odk)
        A_eq = np.zeros((num_demands, num_vars))
        b_eq = np.zeros(num_demands)

        for d_idx, (odk, d_val) in enumerate(unique_odk.items()):
            b_eq[d_idx] = d_val
            for m in [1, 2, 3, 4, 5]:
                key = (odk[0], odk[1], odk[2], m)
                if key in var_indices:
                    A_eq[d_idx, var_indices[key]] = 1.0

        # Capacities
        od_mode_observed = df.groupby(["dms_orig", "dms_dest", "dms_mode"])["tons_2022"].sum().to_dict()
        A_ub = np.zeros((len(od_mode_observed), num_vars))
        b_ub = np.zeros(len(od_mode_observed))

        for idx, (odm, cap_ton) in enumerate(od_mode_observed.items()):
            b_ub[idx] = cap_ton * 1.35
            orig, dest, mode = int(odm[0]), int(odm[1]), int(odm[2])
            for key, v_idx in var_indices.items():
                if key[0] == orig and key[1] == dest and key[3] == mode:
                    A_ub[idx, v_idx] = 1.0

        bounds = [(0, None) for _ in range(num_vars)]
        alphas = np.linspace(0.0, 1.0, num_points)
        pareto_points = []

        for alpha in alphas:
            obj_c = (1.0 - alpha) * (cost_vec / max_c) + alpha * (emiss_vec / max_e)
            res = linprog(obj_c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
            if res.success:
                x_opt = res.x
                actual_cost = float(np.dot(cost_vec, x_opt))
                actual_emiss = float(np.dot(emiss_vec, x_opt))

                # Mode split
                rail_tons = sum(x_opt[i] for i, r in enumerate(flow_records) if r["mode"] == 2)
                truck_tons = sum(x_opt[i] for i, r in enumerate(flow_records) if r["mode"] == 1)
                water_tons = sum(x_opt[i] for i, r in enumerate(flow_records) if r["mode"] == 3)
                total_tons = sum(x_opt)

                pareto_points.append({
                    "alpha_green_weight": round(float(alpha), 2),
                    "policy_label": f"{int((1-alpha)*100)}% Cost / {int(alpha*100)}% Green",
                    "total_logistics_cost": round(actual_cost, 2),
                    "total_co2e_metric_tons": round(actual_emiss, 1),
                    "rail_share_pct": round((rail_tons / total_tons * 100.0) if total_tons > 0 else 0.0, 1),
                    "truck_share_pct": round((truck_tons / total_tons * 100.0) if total_tons > 0 else 0.0, 1),
                    "water_share_pct": round((water_tons / total_tons * 100.0) if total_tons > 0 else 0.0, 1)
                })

        return pareto_points
