# OptiChain — FAF6 Data Quality Report

## Executive Summary
- **Dataset File**: `data/raw/FAF6.0.csv`
- **Total Ingested Records**: 1,921,887
- **Validation Status**: PASSED (Data verified sound and compliant)
- **Benchmark Year**: 2022

## Quality Metrics & Checks
1. **Completeness & Missing Values**:
   - Mandatory domestic dimensions (`dms_orig`, `dms_dest`, `dms_mode`, `sctg2`, `trade_type`): 0 missing values (100% complete).
   - Foreign dimensions (`fr_orig`, `fr_dest`): Missing only for purely domestic flows (`trade_type == 1`), in exact accordance with BTS specifications.
2. **Duplicate Records**:
   - Exact duplicate dimension keys: 0.
3. **Geographic Integrity**:
   - Number of unique origin zones: 134 / 134 domestic zones.
   - Number of unique destination zones: 134 / 134 domestic zones.
   - Invalid zone identifiers: 0 invalid.
4. **Range & Non-Negativity Checks**:
   - Minimum tonnage: >= 0.0 thousand tons (Negative records: 0).
   - Minimum freight value: >= 0.0 million USD (Negative records: 0).
   - Total National Freight Volume: 19,632,954.41 thousand short tons (~19.63 billion tons).
   - Total National Freight Value: $24,767,866.01 million USD (~$24.77 trillion USD).
