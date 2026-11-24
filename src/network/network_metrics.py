"""
Network Science and Graph Analytics Metrics for OptiChain.
Computes in/out-degree, flow-weighted degree, betweenness centrality, PageRank,
and economic concentration indices (HHI).
"""

from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import pandas as pd
import numpy as np
from src.network.geography import FAF6_MODES, FAF6_DOMESTIC_ZONES
from src.data.sctg_codes import get_sctg_description

class FreightNetworkMetrics:
    @staticmethod
    def compute_node_metrics(G: nx.DiGraph) -> pd.DataFrame:
        """
        Compute comprehensive topological and flow-based metrics for each node in the network.
        Also attaches calculated metrics back onto G.nodes[node] for visualization.
        """
        if len(G) == 0:
            return pd.DataFrame()

        in_degree = dict(G.in_degree())
        out_degree = dict(G.out_degree())
        weighted_in = dict(G.in_degree(weight="tons"))
        weighted_out = dict(G.out_degree(weight="tons"))
        weighted_val_in = dict(G.in_degree(weight="value"))
        weighted_val_out = dict(G.out_degree(weight="value"))

        # Betweenness centrality (using distance for shortest logistics path)
        try:
            betweenness = nx.betweenness_centrality(G, weight="distance", normalized=True)
        except Exception:
            betweenness = {n: 0.0 for n in G.nodes()}

        try:
            pagerank = nx.pagerank(G, weight="tons", alpha=0.85)
        except Exception:
            pagerank = {n: 0.0 for n in G.nodes()}

        rows = []
        for node in G.nodes():
            data = G.nodes[node]
            intra_tons = float(data.get("intra_regional_tons", 0.0))
            intra_val = float(data.get("intra_regional_val", 0.0))
            in_t = float(weighted_in.get(node, 0.0))
            out_t = float(weighted_out.get(node, 0.0))
            in_v = float(weighted_val_in.get(node, 0.0))
            out_v = float(weighted_val_out.get(node, 0.0))
            b_cent = float(betweenness.get(node, 0.0))
            p_rank = float(pagerank.get(node, 0.0))
            in_deg = int(in_degree.get(node, 0))
            out_deg = int(out_degree.get(node, 0))

            # Total throughput incorporates inter-regional inflow + outflow + local intra-regional flows
            total_throughput = round(in_t + out_t + intra_tons, 2)
            inter_regional_throughput = round(in_t + out_t, 2)

            # Store metrics directly onto graph node for plot tooltips
            G.nodes[node]["in_degree"] = in_deg
            G.nodes[node]["out_degree"] = out_deg
            G.nodes[node]["total_degree"] = in_deg + out_deg
            G.nodes[node]["inflow_tons"] = round(in_t, 2)
            G.nodes[node]["outflow_tons"] = round(out_t, 2)
            G.nodes[node]["intra_regional_tons"] = round(intra_tons, 2)
            G.nodes[node]["total_throughput_tons"] = total_throughput
            G.nodes[node]["inter_regional_throughput_tons"] = inter_regional_throughput
            G.nodes[node]["betweenness_centrality"] = round(b_cent, 5)
            G.nodes[node]["pagerank"] = round(p_rank, 5)

            rows.append({
                "zone_code": node,
                "name": data.get("name", f"Zone {node}"),
                "state": data.get("state", ""),
                "lat": data.get("lat", 0.0),
                "lon": data.get("lon", 0.0),
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": in_deg + out_deg,
                "inflow_tons": round(in_t, 2),
                "outflow_tons": round(out_t, 2),
                "net_flow_tons": round(out_t - in_t, 2),
                "intra_regional_tons": round(intra_tons, 2),
                "inter_regional_throughput_tons": inter_regional_throughput,
                "total_throughput_tons": total_throughput,
                "inflow_value": round(in_v, 2),
                "outflow_value": round(out_v, 2),
                "betweenness_centrality": round(b_cent, 5),
                "pagerank": round(p_rank, 5)
            })

        df = pd.DataFrame(rows)
        return df.sort_values(by="total_throughput_tons", ascending=False).reset_index(drop=True)

    @staticmethod
    def compute_top_corridors(flows_df: pd.DataFrame, top_n: int = 20,
                              include_mode: bool = True,
                              exclude_intra: bool = False) -> pd.DataFrame:
        """
        Rank top freight corridors by tonnage and economic value.
        Clearly contrasts cargo freight economic value from carrier logistics transportation cost.
        """
        df = flows_df.copy()
        if exclude_intra and "dms_orig" in df.columns and "dms_dest" in df.columns:
            df = df[df["dms_orig"] != df["dms_dest"]]

        group_cols = ["dms_orig", "dms_dest", "orig_name", "dest_name"]
        if include_mode and "dms_mode" in df.columns:
            group_cols.append("dms_mode")

        corridors = df.groupby(group_cols, as_index=False).agg({
            "tons_2022": "sum",
            "value_2022": "sum",
            "distance_miles": "mean",
            "thousand_ton_miles": "sum"
        })

        if "dms_mode" in corridors.columns:
            corridors["mode_name"] = corridors["dms_mode"].map(FAF6_MODES).fillna("Unknown Mode")
        else:
            corridors["mode_name"] = "All Modes Aggregated"

        # Economic Density ($ / ton cargo value)
        corridors["value_per_ton"] = np.where(
            corridors["tons_2022"] > 0,
            (corridors["value_2022"] * 1000.0) / corridors["tons_2022"],
            0.0
        )

        # Carrier Logistics Cost Estimate ($ Millions) based on mode-specific ton-mile rates
        # Truck: ~$0.22/ton-mile, Rail: ~$0.05/ton-mile, Water: ~$0.03/ton-mile, Air: ~$1.20/ton-mile, Multimodal: ~$0.18/ton-mile
        mode_cost_per_ton_mile = {
            1: 0.22, 2: 0.05, 3: 0.03, 4: 1.20, 5: 0.18, 6: 0.02, 7: 0.15, 8: 0.10
        }
        if "dms_mode" in corridors.columns:
            rates = corridors["dms_mode"].map(mode_cost_per_ton_mile).fillna(0.18)
        else:
            rates = 0.18

        # Carrier cost = thousand_ton_miles * 1000 * rate / 1e6 = thousand_ton_miles * rate / 1000 ($ Millions)
        corridors["carrier_transport_cost_mil"] = round(corridors["thousand_ton_miles"] * rates / 1000.0, 3)

        return corridors.sort_values(by="tons_2022", ascending=False).head(top_n).reset_index(drop=True)

    @staticmethod
    def compute_concentration_indices(flows_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute Herfindahl-Hirschman Index (HHI) for commodity and mode shares.
        Formula: HHI = sum( s_i^2 ) where s_i is percentage share (0 - 100).
        
        Official DOJ / FTC Antitrust Guidelines thresholds:
        - HHI < 1,500: Unconcentrated / Diversified (Competitive)
        - 1,500 <= HHI <= 2,500: Moderately Concentrated
        - HHI > 2,500: Highly Concentrated (Monopolistic / Single-mode dependency)
        """
        total_tons = float(flows_df["tons_2022"].sum())
        total_val = float(flows_df["value_2022"].sum()) if "value_2022" in flows_df.columns else 0.0

        if total_tons <= 0:
            return {
                "basis": "freight_tonnage",
                "mode_hhi": 0.0,
                "commodity_hhi": 0.0,
                "corridor_hhi": 0.0,
                "mode_concentration_level": "N/A",
                "commodity_concentration_level": "N/A",
                "mode_shares_df": pd.DataFrame(),
                "commodity_shares_df": pd.DataFrame()
            }

        # 1. Mode Shares (Tonnage & Value)
        mode_agg = flows_df.groupby("dms_mode", as_index=False).agg({
            "tons_2022": "sum",
            "value_2022": "sum" if "value_2022" in flows_df.columns else "count"
        })
        mode_agg["mode_name"] = mode_agg["dms_mode"].map(FAF6_MODES).fillna("Unknown")
        mode_agg["share_tons_pct"] = (mode_agg["tons_2022"] / total_tons) * 100.0
        mode_agg["squared_share_tons"] = mode_agg["share_tons_pct"] ** 2

        if total_val > 0:
            mode_agg["share_val_pct"] = (mode_agg["value_2022"] / total_val) * 100.0
            mode_agg["squared_share_val"] = mode_agg["share_val_pct"] ** 2
            mode_hhi_val = float(mode_agg["squared_share_val"].sum())
        else:
            mode_agg["share_val_pct"] = 0.0
            mode_agg["squared_share_val"] = 0.0
            mode_hhi_val = 0.0

        mode_hhi_tons = float(mode_agg["squared_share_tons"].sum())
        mode_shares_df = mode_agg.sort_values(by="tons_2022", ascending=False).reset_index(drop=True)

        # 2. Commodity Shares (Tonnage & Value)
        comm_agg = flows_df.groupby("sctg2", as_index=False).agg({
            "tons_2022": "sum",
            "value_2022": "sum" if "value_2022" in flows_df.columns else "count"
        })
        comm_agg["commodity_name"] = comm_agg["sctg2"].apply(get_sctg_description)
        comm_agg["share_tons_pct"] = (comm_agg["tons_2022"] / total_tons) * 100.0
        comm_agg["squared_share_tons"] = comm_agg["share_tons_pct"] ** 2

        if total_val > 0:
            comm_agg["share_val_pct"] = (comm_agg["value_2022"] / total_val) * 100.0
            comm_agg["squared_share_val"] = comm_agg["share_val_pct"] ** 2
            comm_hhi_val = float(comm_agg["squared_share_val"].sum())
        else:
            comm_agg["share_val_pct"] = 0.0
            comm_agg["squared_share_val"] = 0.0
            comm_hhi_val = 0.0

        comm_hhi_tons = float(comm_agg["squared_share_tons"].sum())
        commodity_shares_df = comm_agg.sort_values(by="tons_2022", ascending=False).reset_index(drop=True)

        # 3. Corridor HHI (Tonnage)
        corr_shares = (flows_df.groupby(["dms_orig", "dms_dest"])["tons_2022"].sum() / total_tons) * 100.0
        corr_hhi = float((corr_shares ** 2).sum())

        return {
            "basis": "freight_tonnage",
            "mode_hhi": round(mode_hhi_tons, 2),
            "commodity_hhi": round(comm_hhi_tons, 2),
            "corridor_hhi": round(corr_hhi, 2),
            "mode_hhi_value": round(mode_hhi_val, 2),
            "commodity_hhi_value": round(comm_hhi_val, 2),
            "mode_concentration_level": "High" if mode_hhi_tons > 2500 else ("Moderate" if mode_hhi_tons >= 1500 else "Low / Diversified"),
            "commodity_concentration_level": "High" if comm_hhi_tons > 2500 else ("Moderate" if comm_hhi_tons >= 1500 else "Low / Diversified"),
            "mode_shares_df": mode_shares_df,
            "commodity_shares_df": commodity_shares_df,
            "formula_explanation": (
                "HHI is calculated as sum(s_i^2), where s_i is the percentage share (0 to 100%). "
                "Values range from near 0 to 10,000 (pure monopoly). "
                "DOJ/FTC thresholds: <1500 (unconcentrated), 1500-2500 (moderate), >2500 (highly concentrated)."
            )
        }
