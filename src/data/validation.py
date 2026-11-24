"""
Validation Module for FAF6 Data.
Performs data integrity checks: duplicate records, null values,
valid ranges, geographic codes, mode codes, commodity codes, and non-negativity.
"""

from typing import Dict, List, Any, Tuple, Set
import pandas as pd
from src.network.geography import FAF6_DOMESTIC_ZONES, FAF6_MODES

# Official SCTG 2-digit commodities: 1-41, and 43 (Mixed freight)
OFFICIAL_SCTG2_CODES: Set[int] = set(range(1, 42)) | {43}

class FAF6DataValidator:
    def __init__(self):
        self.valid_zones = set(FAF6_DOMESTIC_ZONES.keys())
        self.valid_modes = set(FAF6_MODES.keys())
        self.valid_commodities = OFFICIAL_SCTG2_CODES
        self.valid_trade_types = {1, 2, 3}

    def validate_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run complete battery of validation tests on FAF6 dataframe.
        """
        results = {
            "total_records": len(df),
            "passed": True,
            "issues": [],
            "statistics": {}
        }

        # 1. Required Columns Check
        expected_cols = ["dms_orig", "dms_dest", "dms_mode", "sctg2", "trade_type", "tons_2022", "value_2022"]
        missing_cols = [c for c in expected_cols if c not in df.columns]
        if missing_cols:
            results["passed"] = False
            results["issues"].append(f"Missing mandatory columns: {missing_cols}")
            return results

        # 2. Duplicate Records Check on all 9 categorical dimensions
        all_dims = ["dms_orig", "dms_dest", "dms_mode", "sctg2", "trade_type",
                    "fr_orig", "fr_dest", "fr_inmode", "fr_outmode"]
        active_dims = [c for c in all_dims if c in df.columns]
        
        duplicates_count = int(df.duplicated(subset=active_dims).sum())
        results["statistics"]["duplicate_records"] = duplicates_count
        if duplicates_count > 0:
            results["passed"] = False
            results["issues"].append(f"Found {duplicates_count} duplicate dimension records.")

        # 3. Null Values Check in core fields
        core_nulls = df[expected_cols].isnull().sum().to_dict()
        results["statistics"]["core_null_counts"] = {k: int(v) for k, v in core_nulls.items()}
        for col, null_c in core_nulls.items():
            if null_c > 0:
                results["passed"] = False
                results["issues"].append(f"Column {col} has {null_c} missing/null values.")

        # 4. Geographic Identifiers Validation
        invalid_orig = df[~df["dms_orig"].isin(self.valid_zones)]["dms_orig"].unique().tolist()
        invalid_dest = df[~df["dms_dest"].isin(self.valid_zones)]["dms_dest"].unique().tolist()
        results["statistics"]["invalid_orig_zones"] = invalid_orig
        results["statistics"]["invalid_dest_zones"] = invalid_dest
        if invalid_orig or invalid_dest:
            results["passed"] = False
            results["issues"].append(f"Invalid origin zones: {invalid_orig}, invalid dest zones: {invalid_dest}")

        # 5. Mode and Commodity Validation
        invalid_modes = df[~df["dms_mode"].isin(self.valid_modes)]["dms_mode"].unique().tolist()
        invalid_commodities = df[~df["sctg2"].isin(self.valid_commodities)]["sctg2"].unique().tolist()
        results["statistics"]["invalid_modes"] = invalid_modes
        results["statistics"]["invalid_commodities"] = invalid_commodities
        if invalid_modes or invalid_commodities:
            results["passed"] = False
            results["issues"].append(f"Invalid modes: {invalid_modes}, invalid commodities: {invalid_commodities}")

        # 6. Non-negativity Check
        neg_tons = int((df["tons_2022"] < 0).sum())
        neg_value = int((df["value_2022"] < 0).sum())
        results["statistics"]["negative_tons_count"] = neg_tons
        results["statistics"]["negative_value_count"] = neg_value
        if neg_tons > 0 or neg_value > 0:
            results["passed"] = False
            results["issues"].append(f"Found negative values: tons={neg_tons}, value={neg_value}")

        # Summary statistics
        results["statistics"]["unique_origins"] = int(df["dms_orig"].nunique())
        results["statistics"]["unique_destinations"] = int(df["dms_dest"].nunique())
        results["statistics"]["unique_commodities"] = int(df["sctg2"].nunique())
        results["statistics"]["unique_modes"] = int(df["dms_mode"].nunique())
        results["statistics"]["total_tonnage_thousands"] = float(df["tons_2022"].sum())
        results["statistics"]["total_value_millions"] = float(df["value_2022"].sum())

        return results
