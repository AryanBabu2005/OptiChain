"""
Reproducible Experimental Research Framework for OptiChain.
Executes experiments E1 through E10 on the FAF6 dataset,
records all mathematical metrics, saves results to SQLite, JSON, and CSV.
"""

import os
import json
import time
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import networkx as nx
from src.database.storage import OptiChainDatabase
from src.network.graph_builder import FreightGraphBuilder
from src.network.network_metrics import FreightNetworkMetrics
from src.models.freight_model import MultimodalFreightModel
from src.models.capacity_model import CapacityPlanningModel
from src.models.disruption_model import FreightDisruptionSimulator
from src.algorithms.transportation import TransportationSolver
from src.algorithms.modi import MODISolver

class ExperimentRunner:
    def __init__(self, data_path: str = "data/processed/selected_network.parquet",
                 experiments_dir: str = "data/experiments"):
        self.data_path = data_path
        self.experiments_dir = experiments_dir
        self.db = OptiChainDatabase()
        os.makedirs(self.experiments_dir, exist_ok=True)

    def load_network_data(self) -> pd.DataFrame:
        if os.path.exists(self.data_path):
            return pd.read_parquet(self.data_path)
        demo_path = "data/processed/demo_network.parquet"
        if os.path.exists(demo_path):
            return pd.read_parquet(demo_path)
        raise FileNotFoundError(f"Neither {self.data_path} nor demo dataset found.")

    def run_all_experiments(self) -> List[Dict[str, Any]]:
        """
        Execute E1 through E10 sequentially, recording metrics and persisting outputs.
        """
        df = self.load_network_data()
        results = []

        print("=== EXECUTING OPTICHAIN EXPERIMENTAL RESEARCH BATTERY (E1 - E10) ===")

        # E1: Historical Freight Network Analysis
        print("Running E1: Historical Freight Network Analysis...")
        t0 = time.time()
        G = FreightGraphBuilder.build_graph_from_flows(df)
        node_metrics = FreightNetworkMetrics.compute_node_metrics(G)
        top_corridors = FreightNetworkMetrics.compute_top_corridors(df, top_n=10)
        hhi = FreightNetworkMetrics.compute_concentration_indices(df)
        e1_time = round(time.time() - t0, 3)

        e1_metrics = {
            "total_nodes": len(G.nodes()),
            "total_edges": len(G.edges()),
            "network_density": round(nx.density(G), 4),
            "mode_hhi": hhi["mode_hhi"],
            "commodity_hhi": hhi["commodity_hhi"],
            "top_hub_by_throughput": node_metrics.iloc[0]["name"] if len(node_metrics) > 0 else "N/A",
            "top_hub_throughput_k_tons": float(node_metrics.iloc[0]["total_throughput_tons"]) if len(node_metrics) > 0 else 0.0
        }
        self.db.log_experiment("E1", "Historical Freight Network Analysis", "Network Science", e1_time, "optimal", e1_metrics)
        results.append({"code": "E1", "title": "Historical Freight Network Analysis", "runtime": e1_time, "metrics": e1_metrics})

        # E2: Historical Baseline vs Optimized Allocation
        print("Running E2: Historical Baseline vs Optimized Allocation...")
        t0 = time.time()
        model = MultimodalFreightModel()
        e2_sol = model.build_and_solve(df, capacity_multiplier=1.25)
        e2_time = round(time.time() - t0, 3)

        e2_metrics = {
            "observed_baseline_cost": e2_sol["observed_baseline_cost"],
            "optimized_objective_cost": e2_sol["objective_value"],
            "cost_savings_amount": e2_sol["cost_savings"],
            "cost_savings_percent": e2_sol["savings_percent"],
            "freight_tons_allocated": e2_sol["total_freight_tons"],
            "num_decision_vars": e2_sol["num_decision_vars"]
        }
        self.db.log_experiment("E2", "Historical Baseline vs Optimized Allocation", "Linear Programming", e2_time, e2_sol["status"], e2_metrics)
        results.append({"code": "E2", "title": "Historical Baseline vs Optimized Allocation", "runtime": e2_time, "metrics": e2_metrics})

        # E3: Northwest Corner vs Least Cost vs VAM
        print("Running E3: NWCM vs LCM vs VAM Transportation Comparison...")
        t0 = time.time()
        # Create a representative aggregated 4x4 origin-destination matrix from dataset
        top_origs = df.groupby("dms_orig")["tons_2022"].sum().nlargest(4).index.tolist()
        top_dests = df.groupby("dms_dest")["tons_2022"].sum().nlargest(4).index.tolist()

        c_mat = np.zeros((4, 4))
        for i, o in enumerate(top_origs):
            for j, d in enumerate(top_dests):
                dist = df[(df["dms_orig"] == o) & (df["dms_dest"] == d)]["distance_miles"].mean()
                c_mat[i, j] = dist * 0.18 if not np.isnan(dist) else 300.0

        sup = np.array([120.0, 150.0, 90.0, 140.0])
        dem = np.array([100.0, 160.0, 110.0, 130.0])

        nw_res = TransportationSolver.northwest_corner(c_mat, sup, dem)
        lc_res = TransportationSolver.least_cost(c_mat, sup, dem)
        vam_res = TransportationSolver.vogels_approximation(c_mat, sup, dem)
        modi_res = MODISolver().optimize(c_mat, vam_res["allocation"], vam_res["basic_cells"])
        e3_time = round(time.time() - t0, 3)

        e3_metrics = {
            "nwcm_initial_cost": nw_res["total_cost"],
            "lcm_initial_cost": lc_res["total_cost"],
            "vam_initial_cost": vam_res["total_cost"],
            "modi_optimal_cost": modi_res["optimal_cost"],
            "vam_modi_gap": round(vam_res["total_cost"] - modi_res["optimal_cost"], 2),
            "nwcm_modi_gap": round(nw_res["total_cost"] - modi_res["optimal_cost"], 2)
        }
        self.db.log_experiment("E3", "Transportation Initializations vs MODI", "Transportation Optimization", e3_time, "optimal", e3_metrics)
        results.append({"code": "E3", "title": "Transportation Initializations vs MODI", "runtime": e3_time, "metrics": e3_metrics})

        # E4: Corridor Capacity Reduction (10%, 25%, 50%)
        print("Running E4: Corridor Capacity Reduction (10%, 25%, 50%)...")
        t0 = time.time()
        sim = FreightDisruptionSimulator()
        e4_10 = sim.simulate_disruption(df, capacity_retention=0.90)
        e4_25 = sim.simulate_disruption(df, capacity_retention=0.75)
        e4_50 = sim.simulate_disruption(df, capacity_retention=0.50)
        e4_time = round(time.time() - t0, 3)

        e4_metrics = {
            "retention_90pct_service_ratio": e4_10["resilience_service_ratio"],
            "retention_90pct_cost_increase_pct": e4_10["cost_increase_percent"],
            "retention_75pct_service_ratio": e4_25["resilience_service_ratio"],
            "retention_75pct_cost_increase_pct": e4_25["cost_increase_percent"],
            "retention_50pct_service_ratio": e4_50["resilience_service_ratio"],
            "retention_50pct_cost_increase_pct": e4_50["cost_increase_percent"]
        }
        self.db.log_experiment("E4", "Corridor Capacity Reduction (10%, 25%, 50%)", "Disruption Resilience", e4_time, "optimal", e4_metrics)
        results.append({"code": "E4", "title": "Corridor Capacity Reduction (10%, 25%, 50%)", "runtime": e4_time, "metrics": e4_metrics})

        # E5: Complete Corridor Closure (Top Corridor Severed)
        print("Running E5: Complete Corridor Closure (Top Corridor Severed)...")
        t0 = time.time()
        top_corr = (int(top_corridors.iloc[0]["dms_orig"]), int(top_corridors.iloc[0]["dms_dest"]))
        e5_res = sim.simulate_disruption(df, disrupted_corridors=[top_corr], capacity_retention=0.0)
        e5_time = round(time.time() - t0, 3)

        e5_metrics = {
            "severed_corridor": f"{top_corridors.iloc[0]['orig_name']} -> {top_corridors.iloc[0]['dest_name']}",
            "resilience_service_ratio": e5_res["resilience_service_ratio"],
            "unmet_demand_tons": e5_res["unmet_demand_tons"],
            "cost_increase_amount": e5_res["cost_increase"],
            "cost_increase_percent": e5_res["cost_increase_percent"]
        }
        self.db.log_experiment("E5", "Complete Corridor Closure", "Disruption Resilience", e5_time, "optimal", e5_metrics)
        results.append({"code": "E5", "title": "Complete Corridor Closure", "runtime": e5_time, "metrics": e5_metrics})

        # E6: Transportation-Mode Disruption (Rail Shutdown)
        print("Running E6: Transportation-Mode Disruption (Rail Network Disrupted)...")
        t0 = time.time()
        e6_res = sim.simulate_disruption(df, disrupted_modes=[2], capacity_retention=0.0)
        e6_time = round(time.time() - t0, 3)

        e6_metrics = {
            "disrupted_mode": "Rail (Mode 2)",
            "resilience_service_ratio": e6_res["resilience_service_ratio"],
            "unmet_demand_tons": e6_res["unmet_demand_tons"],
            "cost_increase_amount": e6_res["cost_increase"],
            "cost_increase_percent": e6_res["cost_increase_percent"],
            "truck_substitution_tons": next((m["allocated_tons"] for m in e6_res["mode_shifts"] if m["mode"] == 1), 0.0)
        }
        self.db.log_experiment("E6", "Transportation Mode Disruption (Rail)", "Disruption Resilience", e6_time, "optimal", e6_metrics)
        results.append({"code": "E6", "title": "Transportation Mode Disruption (Rail)", "runtime": e6_time, "metrics": e6_metrics})

        # E7: Capacity Expansion and Shadow-Price Analysis
        print("Running E7: Capacity Expansion & Shadow-Price Analysis...")
        t0 = time.time()
        cap_model = CapacityPlanningModel()
        e7_sol = cap_model.plan_capacity(df, base_capacity_factor=1.0)
        e7_time = round(time.time() - t0, 3)

        e7_metrics = {
            "total_system_cost_with_expansion": e7_sol["total_objective"],
            "transport_operating_cost": e7_sol["transportation_cost"],
            "capital_expansion_expenditure": e7_sol["capacity_expansion_cost"],
            "number_of_expanded_corridors": e7_sol["num_expanded_corridors"],
            "top_recommended_expansion": e7_sol["recommended_expansions_df"].iloc[0]["orig_name"] + " -> " + e7_sol["recommended_expansions_df"].iloc[0]["dest_name"] if len(e7_sol["recommended_expansions_df"]) > 0 else "None"
        }
        self.db.log_experiment("E7", "Capacity Expansion & Shadow-Price Analysis", "Capacity Planning", e7_time, e7_sol["status"], e7_metrics)
        results.append({"code": "E7", "title": "Capacity Expansion & Shadow-Price Analysis", "runtime": e7_time, "metrics": e7_metrics})

        # E8: Cost Sensitivity (+/-10%, +/-20%)
        print("Running E8: Cost Sensitivity Analysis...")
        t0 = time.time()
        from src.optimization.scenario_engine import ScenarioEngine
        scen_engine = ScenarioEngine()
        e8_m20 = scen_engine.run_scenario_comparison(df, cost_delta_pct=-20.0)
        e8_m10 = scen_engine.run_scenario_comparison(df, cost_delta_pct=-10.0)
        e8_p10 = scen_engine.run_scenario_comparison(df, cost_delta_pct=10.0)
        e8_p20 = scen_engine.run_scenario_comparison(df, cost_delta_pct=20.0)
        e8_time = round(time.time() - t0, 3)

        e8_metrics = {
            "cost_minus_20pct_delta": e8_m20["delta"]["percentage_cost_change"],
            "cost_minus_10pct_delta": e8_m10["delta"]["percentage_cost_change"],
            "cost_plus_10pct_delta": e8_p10["delta"]["percentage_cost_change"],
            "cost_plus_20pct_delta": e8_p20["delta"]["percentage_cost_change"]
        }
        self.db.log_experiment("E8", "Cost Sensitivity (+/-10%, +/-20%)", "Sensitivity Analysis", e8_time, "optimal", e8_metrics)
        results.append({"code": "E8", "title": "Cost Sensitivity (+/-10%, +/-20%)", "runtime": e8_time, "metrics": e8_metrics})

        # E9: Demand Sensitivity (+/-10%, +/-20%)
        print("Running E9: Demand Sensitivity Analysis...")
        t0 = time.time()
        e9_m20 = scen_engine.run_scenario_comparison(df, demand_delta_pct=-20.0)
        e9_m10 = scen_engine.run_scenario_comparison(df, demand_delta_pct=-10.0)
        e9_p10 = scen_engine.run_scenario_comparison(df, demand_delta_pct=10.0)
        e9_p20 = scen_engine.run_scenario_comparison(df, demand_delta_pct=20.0)
        e9_time = round(time.time() - t0, 3)

        e9_metrics = {
            "demand_minus_20pct_cost_change": e9_m20["delta"]["percentage_cost_change"],
            "demand_minus_10pct_cost_change": e9_m10["delta"]["percentage_cost_change"],
            "demand_plus_10pct_cost_change": e9_p10["delta"]["percentage_cost_change"],
            "demand_plus_20pct_cost_change": e9_p20["delta"]["percentage_cost_change"]
        }
        self.db.log_experiment("E9", "Demand Sensitivity (+/-10%, +/-20%)", "Sensitivity Analysis", e9_time, "optimal", e9_metrics)
        results.append({"code": "E9", "title": "Demand Sensitivity (+/-10%, +/-20%)", "runtime": e9_time, "metrics": e9_metrics})

        # E10: Combined Disruption Scenarios
        print("Running E10: Combined Multi-Corridor & Surge Disruption...")
        t0 = time.time()
        top_2_corrs = [
            (int(top_corridors.iloc[0]["dms_orig"]), int(top_corridors.iloc[0]["dms_dest"])),
            (int(top_corridors.iloc[1]["dms_orig"]), int(top_corridors.iloc[1]["dms_dest"]))
        ]
        e10_res = sim.simulate_disruption(
            df,
            disrupted_corridors=top_2_corrs,
            disrupted_modes=[3],  # Waterway disrupted
            capacity_retention=0.35,
            cost_surge_factor=1.20,
            demand_surge_factor=1.10
        )
        e10_time = round(time.time() - t0, 3)

        e10_metrics = {
            "scenario": "Multi-corridor closure (top 2) + Waterway outage + 20% fuel surge + 10% demand surge",
            "resilience_service_ratio": e10_res["resilience_service_ratio"],
            "freight_served_tons": e10_res["freight_served_tons"],
            "unmet_demand_tons": e10_res["unmet_demand_tons"],
            "cost_increase_percent": e10_res["cost_increase_percent"],
            "total_system_cost": e10_res["total_objective_cost"]
        }
        self.db.log_experiment("E10", "Combined Multi-Disruption Scenario", "Disruption Resilience", e10_time, "optimal", e10_metrics)
        results.append({"code": "E10", "title": "Combined Multi-Disruption Scenario", "runtime": e10_time, "metrics": e10_metrics})

        # Save all results to JSON and CSV
        json_path = os.path.join(self.experiments_dir, "experiments_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        # Flatten for CSV
        csv_rows = []
        for r in results:
            row = {"experiment_code": r["code"], "title": r["title"], "runtime_seconds": r["runtime"]}
            for k, v in r["metrics"].items():
                row[f"metric_{k}"] = v
            csv_rows.append(row)

        csv_path = os.path.join(self.experiments_dir, "experiments_results.csv")
        pd.DataFrame(csv_rows).to_csv(csv_path, index=False)

        print(f"=== ALL EXPERIMENTS COMPLETED AND SAVED TO {json_path} AND {csv_path} ===")
        return results
