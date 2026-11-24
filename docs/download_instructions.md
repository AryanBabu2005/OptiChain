# OptiChain — FAF6 Download and Ingestion Instructions

## How to Retrieve the Official FAF6 Regional Database
The Freight Analysis Framework (FAF) is produced by the Bureau of Transportation Statistics (BTS) and the Federal Highway Administration (FHWA).

1. **Official Web Portal**:
   Navigate to the BTS FAF download portal:
   `https://www.bts.gov/faf`

2. **Select FAF6 Regional Database**:
   - Select the 2022 Benchmark Regional Database.
   - Download the primary CSV file (`FAF6.0.csv`).
   - Download the official metadata spreadsheet (`FAF6_Metadata.xlsx`).
   - Download the `FAF6 User Guide.pdf`.

3. **Placement**:
   Place the downloaded files in the following directory layout:
   ```
   OptiChain/
     data/
       raw/
         FAF6.0.csv
         FAF6 User Guide.pdf
       metadata/
         FAF6_Metadata.xlsx
   ```

4. **Run Automated Ingestion**:
   Execute the ingestion pipeline:
   ```bash
   python -c "from src.data.ingestion import FAF6IngestionPipeline; FAF6IngestionPipeline().run_pipeline()"
   ```
   This will validate cryptographic hashes, run schema and range checks, and generate optimized Parquet analytical files.
