"""
CSV Export Utilities for OptiChain.
Converts optimization allocations, corridor metrics, capacity findings,
and scenario summaries into clean, reproducible CSV datasets.
"""

import os
from typing import Dict, Any, List, Union
import pandas as pd

def export_dataframe_to_csv(df: pd.DataFrame, filepath: str) -> str:
    """Export pandas DataFrame to CSV with directory creation."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    df.to_csv(filepath, index=False)
    return filepath

def export_dict_list_to_csv(data: List[Dict[str, Any]], filepath: str) -> str:
    """Export list of dictionaries to CSV."""
    df = pd.DataFrame(data)
    return export_dataframe_to_csv(df, filepath)
