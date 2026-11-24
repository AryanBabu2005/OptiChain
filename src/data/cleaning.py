"""
Data Cleaning and Aggregation Module for OptiChain.
Transforms raw FAF6 data into high-performance analytical Parquet datasets.
"""

import os
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from src.network.geography import FAF6_DOMESTIC_ZONES, get_corridor_distance, get_zone_name

class FAF6DataCleaner:
    def __init__(self, raw_df: pd.DataFrame):
        self.df = raw_df.copy()

    def clean_dataset(self) -> pd.DataFrame:
        """
        Clean and cast types of the raw FAF6 dataset.
        """
        df = self.df

        # Clean nulls in foreign columns by filling with 0 or -1
        foreign_cols = ["fr_orig", "fr_dest", "fr_inmode", "fr_outmode"]
        for col in foreign_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype("int32")

        # Cast core categorical fields to optimal integer types
        df["dms_orig"] = df["dms_orig"].astype("int32")
        df["dms_dest"] = df["dms_dest"].astype("int32")
        df["dms_mode"] = df["dms_mode"].astype("int16")
        df["sctg2"] = df["sctg2"].astype("int16")
        df["trade_type"] = df["trade_type"].astype("int16")

        # Ensure float64 for tonnage and value
        df["tons_2022"] = df["tons_2022"].astype("float64")
        df["value_2022"] = df["value_2022"].astype("float64")

        # Clip any minuscule negative values to 0
        df["tons_2022"] = df["tons_2022"].clip(lower=0.0)
        df["value_2022"] = df["value_2022"].clip(lower=0.0)

        # Aggregate duplicates if any exist
        key_cols = ["dms_orig", "dms_dest", "dms_mode", "sctg2", "trade_type", "fr_orig", "fr_dest"]
        existing_keys = [c for c in key_cols if c in df.columns]
        if df.duplicated(subset=existing_keys).any():
            df = df.groupby(existing_keys, as_index=False).agg({
                "tons_2022": "sum",
                "value_2022": "sum"
            })

        return df

    @staticmethod
    def aggregate_domestic_flows(cleaned_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate domestic flows (trade_type == 1) by origin, destination, commodity, and mode.
        """
        dom_df = cleaned_df[cleaned_df["trade_type"] == 1].copy()
        agg = dom_df.groupby(["dms_orig", "dms_dest", "sctg2", "dms_mode", "trade_type"], as_index=False).agg({
            "tons_2022": "sum",
            "value_2022": "sum"
        })

        # Add origin and destination names
        agg["orig_name"] = agg["dms_orig"].map(lambda z: get_zone_name(z))
        agg["dest_name"] = agg["dms_dest"].map(lambda z: get_zone_name(z))
        
        # Add distance
        agg["distance_miles"] = agg.apply(
            lambda r: get_corridor_distance(int(r["dms_orig"]), int(r["dms_dest"]), int(r["dms_mode"])),
            axis=1
        )
        # Ton-miles in thousands
        agg["thousand_ton_miles"] = agg["tons_2022"] * agg["distance_miles"]
        return agg

    @staticmethod
    def create_selected_network(flows_df: pd.DataFrame, top_zones_count: int = 20) -> pd.DataFrame:
        """
        Extract a representative research network subset comprising the top domestic freight hubs
        and major corridors for intensive multi-commodity LP optimization experiments.
        """
        # Find top freight hubs by total tonnage (orig + dest)
        orig_tons = flows_df.groupby("dms_orig")["tons_2022"].sum()
        dest_tons = flows_df.groupby("dms_dest")["tons_2022"].sum()
        total_hub_tons = orig_tons.add(dest_tons, fill_value=0).sort_values(ascending=False)
        
        top_hubs = set(total_hub_tons.head(top_zones_count).index)

        # Filter flows between these major hubs
        subset = flows_df[
            flows_df["dms_orig"].isin(top_hubs) & flows_df["dms_dest"].isin(top_hubs)
        ].copy()

        # Filter out minor tail commodities to keep top 10 most impactful commodities
        top_commodities = subset.groupby("sctg2")["tons_2022"].sum().sort_values(ascending=False).head(10).index
        subset = subset[subset["sctg2"].isin(top_commodities)].copy()

        # Keep primary freight modes (Truck=1, Rail=2, Water=3, Air=4, Multimodal=5)
        subset = subset[subset["dms_mode"].isin([1, 2, 3, 4, 5])].copy()

        return subset

    @staticmethod
    def create_demonstration_dataset() -> pd.DataFrame:
        """
        Create a compact, mathematically rigorous demonstration dataset
        for instant testing and validation before full pipeline loading.
        Clearly labeled as synthetic demonstration data derived from real FAF6 parameters.
        """
        # 6 Iconic US Hubs: Chicago (171), Los Angeles (61), New York (363), Houston (486), Atlanta (131), Seattle (531)
        hubs = [171, 61, 363, 486, 131, 531]
        commodities = [2, 7, 26]  # Cereal grains (2), Other foodstuffs (7), Plastics/rubber (26)
        modes = [1, 2, 3]  # Truck (1), Rail (2), Water (3)

        records = []
        np.random.seed(42)

        for orig in hubs:
            for dest in hubs:
                if orig == dest:
                    continue
                dist = get_corridor_distance(orig, dest, 1)
                for comm in commodities:
                    # Deterministic base flow based on hub pair and distance
                    base_tons = 150.0 + (orig * dest % 73) * 5.0 - (dist * 0.05)
                    base_tons = max(base_tons, 25.0)

                    # Truck flow
                    records.append({
                        "dms_orig": orig,
                        "dms_dest": dest,
                        "orig_name": get_zone_name(orig),
                        "dest_name": get_zone_name(dest),
                        "sctg2": comm,
                        "dms_mode": 1,
                        "trade_type": 1,
                        "distance_miles": dist,
                        "tons_2022": round(base_tons * 0.65, 2),
                        "value_2022": round(base_tons * 0.65 * 1.8, 2),
                        "thousand_ton_miles": round(base_tons * 0.65 * dist, 2),
                        "is_demonstration": True
                    })

                    # Rail flow (for distances > 300 miles)
                    if dist > 300:
                        rail_dist = get_corridor_distance(orig, dest, 2)
                        records.append({
                            "dms_orig": orig,
                            "dms_dest": dest,
                            "orig_name": get_zone_name(orig),
                            "dest_name": get_zone_name(dest),
                            "sctg2": comm,
                            "dms_mode": 2,
                            "trade_type": 1,
                            "distance_miles": rail_dist,
                            "tons_2022": round(base_tons * 0.35, 2),
                            "value_2022": round(base_tons * 0.35 * 1.2, 2),
                            "thousand_ton_miles": round(base_tons * 0.35 * rail_dist, 2),
                            "is_demonstration": True
                        })

                    # Water flow (coastal / river pairs e.g. Houston, LA, NY, Seattle, Chicago)
                    coastal_hubs = {61, 363, 486, 531, 171}
                    if orig in coastal_hubs and dest in coastal_hubs and comm in [2, 26]:
                        water_dist = get_corridor_distance(orig, dest, 3)
                        records.append({
                            "dms_orig": orig,
                            "dms_dest": dest,
                            "orig_name": get_zone_name(orig),
                            "dest_name": get_zone_name(dest),
                            "sctg2": comm,
                            "dms_mode": 3,
                            "trade_type": 1,
                            "distance_miles": water_dist,
                            "tons_2022": round(base_tons * 0.20, 2),
                            "value_2022": round(base_tons * 0.20 * 0.9, 2),
                            "thousand_ton_miles": round(base_tons * 0.20 * water_dist, 2),
                            "is_demonstration": True
                        })

        demo_df = pd.DataFrame(records)
        return demo_df
