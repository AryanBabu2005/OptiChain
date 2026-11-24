# OptiChain — FAF6 Data Provenance & Lineage

## Source Provenance
- **Dataset Title**: Freight Analysis Framework Version 6 (FAF6.0)
- **Publisher**: Bureau of Transportation Statistics (BTS), U.S. Department of Transportation, and Federal Highway Administration (FHWA).
- **Official Source URL**: https://www.bts.gov/faf
- **Benchmark Release Year**: 2022
- **Raw CSV File**: `data/raw/FAF6.0.csv` (76,414,171 bytes)
- **Raw CSV SHA256**: `bbe7e2c173486fd8d1fd70103af4f0a494b58b5a8cfb43855d11eebd741834ab`
- **Metadata File**: `data/metadata/FAF6_Metadata.xlsx` (28,609 bytes)
- **Metadata SHA256**: `8c555ebfbd03bccb46f9f80e12f555516bd38dbb93ec75feff5797cd7027479a`
- **User Guide**: `data/raw/FAF6 User Guide.pdf` (319,526 bytes)
- **Ingestion Timestamp**: `2026-11-17T13:23:33.394830`

## Data Lineage Pipeline
```
[Raw FAF6.0.csv (76.4 MB)] + [FAF6_Metadata.xlsx]
                │
                ▼
      [Data Provenance & Checksum]
                │
                ▼
    [Schema & Range Validation]
                │
                ▼
   [Type Casting & Duplication Handling]
                │
     ┌──────────┴──────────────────────────┐
     ▼                                     ▼
[faf6_cleaned.parquet]          [freight_flows.parquet]
(1.92M records)                 (Aggregated domestic flows)
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
            [selected_network.parquet]             [demo_network.parquet]
            (Top 20 hubs research subset)          (Labelled demo dataset)
```
