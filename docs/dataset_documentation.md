# OptiChain: FAF6 Dataset Documentation

## 1. Dataset Overview
- **Name**: Freight Analysis Framework Version 6 (FAF6.0) Regional Database
- **Benchmark Year**: 2022
- **Publisher**: Bureau of Transportation Statistics (BTS), U.S. Department of Transportation, and Federal Highway Administration (FHWA)
- **Official Portal**: https://www.bts.gov/faf
- **Ingested File**: `data/raw/FAF6.0.csv` (76.4 MB, 1,921,887 records)
- **Metadata File**: `data/metadata/FAF6_Metadata.xlsx` (28.6 KB)
- **User Guide**: `data/raw/FAF6 User Guide.pdf` (319.5 KB)

## 2. Geography & Spatial Aggregation
FAF6 divides the United States into **134 Domestic FAF Zones**:
- Major metropolitan statistical areas (MSAs) or Consolidated Metropolitan Areas (CFS areas) such as Chicago IL, Los Angeles CA, New York NY, Houston TX, Atlanta GA.
- Balance-of-State / Remainder-of-State regions for areas outside designated CFS metropolitan areas (e.g. Rest of Illinois, Rest of California, Rest of Texas).
- Centroid coordinates (latitude, longitude) for all 134 zones are verified in `src/network/geography.py` to calculate exact great-circle and mode-adjusted corridor network route distances.

## 3. Classification Dimensions
1. **Trade Types (`trade_type`)**:
   - `1`: Domestic flows (shipped between domestic origins and destinations).
   - `2`: Import flows (originate in foreign zone, enter via domestic entry port).
   - `3`: Export flows (shipped from domestic origin, exit via domestic export port).
2. **Transportation Modes (`dms_mode`)**:
   - `1`: Truck (for-hire, private carrier, customer pick-up)
   - `2`: Rail (carload, intermodal, unit train)
   - `3`: Water (shallow-draft inland waterways, deep-draft coastal/Great Lakes)
   - `4`: Air (commercial freight and truck-air express)
   - `5`: Multiple modes & mail (intermodal rail-truck containers, parcel mail)
   - `6`: Pipeline (crude oil, natural gas, refined petroleum)
   - `7`: Other and unknown
   - `8`: No domestic mode
3. **Commodity Categories (`sctg2`)**:
   - 42 standard categories under the Standard Classification of Transported Goods (SCTG):
     - Agriculture: 01 (Live animals), 02 (Cereal grains), 03 (Other agricultural products), 04 (Animal feed).
     - Food & Beverages: 05 (Meat/seafood), 06 (Milled grains), 07 (Other foodstuffs), 08 (Alcoholic beverages).
     - Energy & Raw Materials: 10 (Stone), 11 (Sand/gravel), 12 (Gravel), 13 (Nonmetallic minerals), 14 (Metallic ores), 15 (Coal), 16 (Crude petroleum).
     - Manufactured Goods: 20 (Basic chemicals), 24 (Plastics), 30 (Textiles), 34 (Machinery), 35 (Electronics), 36 (Motor vehicles).
     - Mixed Freight: Code 43 (Mixed parcel shipments).

## 4. Analytical Units
- `tons_2022`: Thousand Short Tons ($1 \text{ unit} = 1,000 \text{ short tons} = 2,000,000 \text{ lbs}$).
- `value_2022`: Millions of 2022 Constant US Dollars ($1 \text{ unit} = \$1,000,000 \text{ USD}$).
- `distance_miles`: Mode-adjusted network corridor route distance (statute miles).
- `thousand_ton_miles`: Product of freight weight and corridor distance ($T \times D$).
