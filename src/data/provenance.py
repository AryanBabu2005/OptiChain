"""
Data Provenance and Metadata Tracker for OptiChain FAF6 Ingestion.
Records exact cryptographic hashes, source metadata, and processing timestamps.
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any

class DataProvenanceTracker:
    def __init__(self, raw_data_dir: str = "data/raw", metadata_dir: str = "data/metadata"):
        self.raw_data_dir = raw_data_dir
        self.metadata_dir = metadata_dir

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        """Compute SHA256 checksum for a file."""
        if not os.path.exists(filepath):
            return ""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_source_provenance(self) -> Dict[str, Any]:
        """Collect source provenance metadata."""
        raw_csv = os.path.join(self.raw_data_dir, "FAF6.0.csv")
        meta_xlsx = os.path.join(self.metadata_dir, "FAF6_Metadata.xlsx")
        user_guide = os.path.join(self.raw_data_dir, "FAF6 User Guide.pdf")

        csv_exists = os.path.exists(raw_csv)
        meta_exists = os.path.exists(meta_xlsx)
        guide_exists = os.path.exists(user_guide)

        csv_hash = self.compute_sha256(raw_csv) if csv_exists else ""
        meta_hash = self.compute_sha256(meta_xlsx) if meta_exists else ""
        guide_hash = self.compute_sha256(user_guide) if guide_exists else ""

        provenance = {
            "platform": "OptiChain",
            "benchmark_year": 2022,
            "dataset_name": "Freight Analysis Framework Version 6 (FAF6.0)",
            "publisher": "U.S. Department of Transportation, Bureau of Transportation Statistics (BTS) & Federal Highway Administration (FHWA)",
            "official_url": "https://www.bts.gov/faf",
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {
                "raw_csv": {
                    "path": raw_csv,
                    "exists": csv_exists,
                    "size_bytes": os.path.getsize(raw_csv) if csv_exists else 0,
                    "sha256": csv_hash
                },
                "metadata_file": {
                    "path": meta_xlsx,
                    "exists": meta_exists,
                    "size_bytes": os.path.getsize(meta_xlsx) if meta_exists else 0,
                    "sha256": meta_hash
                },
                "user_guide": {
                    "path": user_guide,
                    "exists": guide_exists,
                    "size_bytes": os.path.getsize(user_guide) if guide_exists else 0,
                    "sha256": guide_hash
                }
            },
            "schema_expected": [
                "fr_orig", "dms_orig", "dms_dest", "fr_dest",
                "fr_inmode", "dms_mode", "fr_outmode", "sctg2",
                "trade_type", "tons_2022", "value_2022"
            ],
            "units": {
                "tons_2022": "Thousand Short Tons (1,000 short tons = 2,000,000 lbs)",
                "value_2022": "Millions of 2022 Constant US Dollars",
                "dms_orig": "FAF6 Domestic Zone Code (11 to 560)",
                "dms_dest": "FAF6 Domestic Zone Code (11 to 560)",
                "sctg2": "Standard Classification of Transported Goods (SCTG) 2-digit code (1 to 42)",
                "dms_mode": "FAF6 Domestic Mode Code (1 to 8)",
                "trade_type": "1 = Domestic, 2 = Import, 3 = Export"
            }
        }
        return provenance
