"""
NetworkX Graph Builder for OptiChain Freight Networks.
Constructs directed freight flow graphs with comprehensive node and edge attributes.
"""

from typing import Dict, Any, Optional
import networkx as nx
import pandas as pd
from src.network.geography import FAF6_DOMESTIC_ZONES, get_zone_name, get_zone_coords

class FreightGraphBuilder:
    @staticmethod
    def build_graph_from_flows(flows_df: pd.DataFrame, min_tonnage: float = 0.0,
                               exclude_self_loops: bool = True) -> nx.DiGraph:
        """
        Build a directed NetworkX graph from a freight flows dataframe.
        Nodes: FAF6 Domestic Regions (Representative Points)
        Edges: Directed freight corridors with aggregated tons, value, and ton-miles.
        
        Args:
            flows_df: Parquet freight flows DataFrame.
            min_tonnage: Minimum corridor tonnage threshold.
            exclude_self_loops: If True, excludes intra-regional flows (dms_orig == dms_dest)
                                from network corridor edges, while preserving them in node attributes.
        """
        G = nx.DiGraph(name="FAF6_Freight_Network")

        # 1. Compute intra-regional flows (self-loops) separately for node accounting
        intra_df = flows_df[flows_df["dms_orig"] == flows_df["dms_dest"]]
        intra_by_node = intra_df.groupby("dms_orig")["tons_2022"].sum().to_dict()
        intra_val_by_node = intra_df.groupby("dms_orig")["value_2022"].sum().to_dict()

        # 2. Filter corridors based on self-loop configuration
        if exclude_self_loops:
            corridor_source = flows_df[flows_df["dms_orig"] != flows_df["dms_dest"]].copy()
        else:
            corridor_source = flows_df.copy()

        corridor_df = corridor_source.groupby(["dms_orig", "dms_dest"], as_index=False).agg({
            "tons_2022": "sum",
            "value_2022": "sum",
            "thousand_ton_miles": "sum",
            "distance_miles": "mean"
        })

        if min_tonnage > 0:
            corridor_df = corridor_df[corridor_df["tons_2022"] >= min_tonnage]

        # 3. Add Nodes with spatial and administrative metadata
        all_unique_nodes = sorted(list(set(flows_df["dms_orig"]).union(set(flows_df["dms_dest"]))))
        for node in all_unique_nodes:
            z_info = FAF6_DOMESTIC_ZONES.get(int(node), {})
            G.add_node(
                int(node),
                name=z_info.get("name", f"Zone {node}"),
                state=z_info.get("state", "US"),
                state_fips=z_info.get("state_fips", 0),
                lat=z_info.get("lat", 0.0),
                lon=z_info.get("lon", 0.0),
                intra_regional_tons=float(intra_by_node.get(node, 0.0)),
                intra_regional_val=float(intra_val_by_node.get(node, 0.0))
            )

        # 4. Add Edges with flow weights
        for _, row in corridor_df.iterrows():
            u = int(row["dms_orig"])
            v = int(row["dms_dest"])
            tons = float(row["tons_2022"])
            G.add_edge(
                u, v,
                weight=tons,
                tons=tons,
                value=float(row["value_2022"]),
                ton_miles=float(row["thousand_ton_miles"]),
                distance=float(row["distance_miles"])
            )

        # 5. Store topological accounting metadata directly on graph
        total_nodes = len(all_unique_nodes)
        total_possible = total_nodes * total_nodes
        inter_possible = total_nodes * (total_nodes - 1)
        
        all_pairs = flows_df.groupby(["dms_orig", "dms_dest"])["tons_2022"].sum()
        active_inter = len([k for k, v in all_pairs.items() if k[0] != k[1] and v > 0])
        zero_flow_inter = max(0, inter_possible - active_inter)

        G.graph["total_regions"] = total_nodes
        G.graph["total_corridor_combinations"] = total_possible
        G.graph["inter_regional_combinations"] = inter_possible
        G.graph["active_directed_corridors"] = active_inter
        G.graph["intra_regional_zones"] = len(intra_by_node)
        G.graph["zero_flow_corridors"] = zero_flow_inter
        G.graph["total_tons"] = float(flows_df["tons_2022"].sum())
        G.graph["intra_regional_tons"] = float(intra_df["tons_2022"].sum())
        G.graph["inter_regional_tons"] = float(flows_df[flows_df["dms_orig"] != flows_df["dms_dest"]]["tons_2022"].sum())

        return G
