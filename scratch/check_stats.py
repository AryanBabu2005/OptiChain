import pandas as pd
import os

print("=== selected_network.parquet ===")
df = pd.read_parquet('data/processed/selected_network.parquet')
print(f"Total Rows: {len(df):,}")
total_k_tons = df['tons_2022'].sum()
total_m_val = df['value_2022'].sum()
print(f"Total Tonnage: {total_k_tons:,.2f} thousand short tons ({total_k_tons / 1e6:.3f} Billion short tons)")
print(f"Total Freight Value: ${total_m_val:,.2f} Million (${total_m_val / 1e6:.3f} Trillion constant 2022 USD)")

origs = set(df['dms_orig'].unique())
dests = set(df['dms_dest'].unique())
all_zones = origs.union(dests)
print(f"Unique Origins: {len(origs)}, Unique Destinations: {len(dests)}, Total Unique Zones: {len(all_zones)}")

# OD pairs
od = df.groupby(['dms_orig', 'dms_dest'])['tons_2022'].sum().reset_index()
print(f"Total OD pairs in table: {len(od)}")
active_od = od[od['tons_2022'] > 0]
print(f"Active OD pairs (flow > 0): {len(active_od)}")
inter_od = active_od[active_od['dms_orig'] != active_od['dms_dest']]
print(f"Active Inter-regional Corridors (orig != dest, flow > 0): {len(inter_od)}")
intra_od = active_od[active_od['dms_orig'] == active_od['dms_dest']]
print(f"Intra-regional connections (orig == dest): {len(intra_od)}")

# Corridors by mode
od_mode = df.groupby(['dms_orig', 'dms_dest', 'dms_mode'])['tons_2022'].sum().reset_index()
active_od_mode = od_mode[(od_mode['tons_2022'] > 0) & (od_mode['dms_orig'] != od_mode['dms_dest'])]
print(f"Active Inter-regional (OD, Mode) corridors: {len(active_od_mode)}")

# Top modes
mode_summary = df.groupby('dms_mode')['tons_2022'].sum().sort_values(ascending=False)
print("\nModal Breakdown (k tons):")
print(mode_summary)

# Top commodities
comm_summary = df.groupby('sctg2')['tons_2022'].sum().sort_values(ascending=False).head(5)
print("\nTop 5 Commodities (k tons):")
print(comm_summary)

# Top OD corridors
top_corridors = df[df['dms_orig'] != df['dms_dest']].groupby(['orig_name', 'dest_name'])['tons_2022'].sum().sort_values(ascending=False).head(5)
print("\nTop 5 Inter-regional OD Corridors (k tons):")
print(top_corridors)

if os.path.exists('data/processed/freight_flows.parquet'):
    print("\n=== freight_flows.parquet (Full Cleaned Dataset) ===")
    ff = pd.read_parquet('data/processed/freight_flows.parquet')
    print(f"Total Rows: {len(ff):,}")
    ff_tons = ff['tons_2022'].sum()
    ff_val = ff['value_2022'].sum()
    print(f"Full Total Tonnage: {ff_tons:,.2f} k tons ({ff_tons / 1e6:.2f} Billion tons)")
    print(f"Full Total Value: ${ff_val:,.2f} M (${ff_val / 1e6:.2f} Trillion)")
    ff_zones = set(ff['dms_orig']).union(set(ff['dms_dest']))
    print(f"Full Geographic Zones: {len(ff_zones)}")
    ff_od = ff.groupby(['dms_orig', 'dms_dest'])['tons_2022'].sum().reset_index()
    print(f"Full Active OD pairs: {len(ff_od[ff_od['tons_2022'] > 0])}")
    print(f"Full Inter-regional OD (orig != dest, flow > 0): {len(ff_od[(ff_od['tons_2022'] > 0) & (ff_od['dms_orig'] != ff_od['dms_dest'])])}")
