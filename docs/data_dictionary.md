# OptiChain — FAF6 Data Dictionary

## 1. Overview
This dictionary documents the variables, classifications, and units for the Freight Analysis Framework Version 6 (FAF6.0) 2022 Benchmark dataset used in OptiChain.

| Column Name | Data Type | Units / Range | Description |
|---|---|---|---|
| `fr_orig` | Integer | 801-808 (or 0) | Foreign region of origin (for import flows). |
| `dms_orig` | Integer | 11-560 | Domestic origin FAF region or entry port. |
| `dms_dest` | Integer | 11-560 | Domestic destination FAF region or exit port. |
| `fr_dest` | Integer | 801-808 (or 0) | Foreign destination region (for export flows). |
| `fr_inmode` | Integer | 1-8 (or 0) | Mode used between foreign origin and US entry region. |
| `dms_mode` | Integer | 1-8 | Mode used for the domestic portion of movement. |
| `fr_outmode` | Integer | 1-8 (or 0) | Mode used between US exit region and foreign destination. |
| `sctg2` | Integer | 1-42 | Commodity classified by SCTG 2-digit code. |
| `trade_type` | Integer | 1, 2, 3 | 1: Domestic, 2: Import, 3: Export. |
| `tons_2022` | Float | Thousand Short Tons | Freight weight moved in 2022 (1 unit = 1,000 short tons). |
| `value_2022` | Float | Million 2022 US$ | Freight economic value moved in 2022. |
| `distance_miles` | Float | Statute Miles | Mode-adjusted network corridor route distance. |
| `thousand_ton_miles` | Float | Thousand Ton-Miles | Product of tonnage and distance (`tons_2022 * distance_miles`). |

## 2. Transportation Modes (`dms_mode`)
- `1`: Truck (for-hire, private carrier, customer pick-up)
- `2`: Rail (carload, intermodal, unit train)
- `3`: Water (shallow draft inland waterway, deep draft coastal/Great Lakes)
- `4`: Air (commercial air freight including truck-air)
- `5`: Multiple modes & mail (intermodal container, postal, courier)
- `6`: Pipeline (crude petroleum, natural gas, refined petroleum products)
- `7`: Other and unknown
- `8`: No domestic mode

## 3. Commodity Categories (`sctg2`)
SCTG (Standard Classification of Transported Goods) two-digit hierarchy spanning 42 codes (01: Live animals/fish to 42: Miscellaneous manufactured products).
