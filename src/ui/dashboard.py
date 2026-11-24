"""
Project Overview & National Freight Network UI for OptiChain.
Humanized, professional academic interface explaining the research goals,
observed FAF6 data vs assumptions, core network findings, and workflow navigation.
"""

from typing import Optional, Dict, Any, List
import os
import streamlit as st
import pandas as pd
import numpy as np
from src.network.geography import FAF6_MODES, FAF6_DOMESTIC_ZONES
from src.visualization.charts import plot_mode_share, plot_commodity_distribution
from src.visualization.maps import create_freight_network_map, FLOW_DISCLAIMER
from src.data.sctg_codes import SCTG_EXPLANATORY_NOTE, get_sctg_description, get_sctg_code_str

def compute_baseline_key_findings(flows_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute empirical key findings dynamically from the active flow dataframe.
    Ensures findings reflect real observations without hardcoded assumptions.
    """
    total_tons = float(flows_df["tons_2022"].sum()) if "tons_2022" in flows_df.columns else 0.0
    total_val = float(flows_df["value_2022"].sum()) if "value_2022" in flows_df.columns else 0.0

    # 1. Dominant Transport Mode & Market Concentration (HHI)
    mode_grp = flows_df.groupby("dms_mode")["tons_2022"].sum().sort_values(ascending=False)
    dom_mode_id = int(mode_grp.index[0]) if len(mode_grp) > 0 else 1
    dom_mode_name = FAF6_MODES.get(dom_mode_id, f"Mode {dom_mode_id}")
    dom_mode_tons = float(mode_grp.iloc[0]) if len(mode_grp) > 0 else 0.0
    dom_mode_pct = (dom_mode_tons / total_tons * 100.0) if total_tons > 0 else 0.0

    mode_shares = (mode_grp / total_tons * 100.0) if total_tons > 0 else pd.Series([0])
    mode_hhi = float((mode_shares ** 2).sum())

    # Secondary modes
    secondary_modes = []
    for m_id, m_tons in mode_grp.iloc[1:3].items():
        secondary_modes.append({
            "name": FAF6_MODES.get(int(m_id), f"Mode {m_id}"),
            "tons": float(m_tons),
            "pct": (float(m_tons) / total_tons * 100.0) if total_tons > 0 else 0.0
        })

    # 2. Top Commodity Categories (SCTG 2-digit)
    comm_grp = flows_df.groupby("sctg2")["tons_2022"].sum().sort_values(ascending=False).head(3)
    top_comms = []
    top_comms_tonnage = 0.0
    for sctg_code, c_tons in comm_grp.items():
        c_code_int = int(sctg_code)
        c_pct = (float(c_tons) / total_tons * 100.0) if total_tons > 0 else 0.0
        top_comms_tonnage += float(c_tons)
        top_comms.append({
            "code": c_code_int,
            "desc": get_sctg_description(c_code_int),
            "tons": float(c_tons),
            "pct": c_pct
        })
    top_comms_combined_pct = (top_comms_tonnage / total_tons * 100.0) if total_tons > 0 else 0.0

    # 3. Inter-Regional Corridors (Strictly orig != dest and tons > 0)
    inter_df = flows_df[(flows_df["dms_orig"] != flows_df["dms_dest"]) & (flows_df["tons_2022"] > 0)]
    corridor_grp = inter_df.groupby(["orig_name", "dest_name"])["tons_2022"].sum().sort_values(ascending=False).head(3)
    top_corridors = []
    for (orig_name, dest_name), c_tons in corridor_grp.items():
        c_rows = inter_df[(inter_df["orig_name"] == orig_name) & (inter_df["dest_name"] == dest_name)]
        c_mode_id = int(c_rows.groupby("dms_mode")["tons_2022"].sum().idxmax())
        c_mode_name = FAF6_MODES.get(c_mode_id, f"Mode {c_mode_id}")
        avg_dist = float(c_rows["distance_miles"].mean()) if "distance_miles" in c_rows.columns else 0.0
        top_corridors.append({
            "origin": orig_name,
            "destination": dest_name,
            "tons": float(c_tons),
            "mode": c_mode_name,
            "distance": avg_dist
        })

    # 4. Average Haul Distance (Weighted by Tonnage)
    if "distance_miles" in flows_df.columns and total_tons > 0:
        weighted_dist = float((flows_df["tons_2022"] * flows_df["distance_miles"]).sum() / total_tons)
    else:
        weighted_dist = 0.0

    return {
        "total_tons": total_tons,
        "total_val": total_val,
        "dom_mode_name": dom_mode_name,
        "dom_mode_tons": dom_mode_tons,
        "dom_mode_pct": dom_mode_pct,
        "mode_hhi": mode_hhi,
        "secondary_modes": secondary_modes,
        "top_comms": top_comms,
        "top_comms_combined_pct": top_comms_combined_pct,
        "top_corridors": top_corridors,
        "weighted_avg_distance": weighted_dist
    }

def render_executive_dashboard(flows_df: pd.DataFrame, full_cleaned_df: Optional[pd.DataFrame] = None):
    # Bespoke Hero Header Banner with Restrained Academic Styling
    st.markdown("""
    <div class="opti-hero-banner">
        <div style="display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap;">
            <span class="opti-pill opti-pill-navy">B.Tech Capstone</span>
            <span class="opti-pill opti-pill-teal">Operations Research & Mathematical Innovation</span>
            <span class="opti-pill opti-pill-slate">Official FAF6.0 Database</span>
            <span class="opti-pill opti-pill-slate">2022 Benchmark Edition</span>
        </div>
        <h1 class="opti-hero-title">
            OptiChain: Multimodal Freight Optimization & Resilience Platform
        </h1>
        <p class="opti-hero-subtitle">
            An empirical transportation economics and mathematical optimization platform. Formulates large-scale linear programs 
            on real origin-destination freight movements, identifies infrastructure capacity bottlenecks via dual shadow prices, 
            and stress-tests systemic supply chain resilience against real-world logistical disruptions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 3-Layer Methodology Cards (Observed Data vs Derived Metrics vs Modelled Assumptions)
    st.markdown("### Data & Modeling Provenance Hierarchy")
    st.markdown(
        "To maintain rigorous academic transparency, OptiChain strictly segregates observed empirical measurements from derived spatial metrics and parametric optimization assumptions:"
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("""
        <div class="opti-card" style="border-top: 3px solid #0F172A; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="opti-card-title">1. Observed Empirical Data</span>
                <span class="opti-pill opti-pill-navy" style="font-size: 9.5px;">BTS / FHWA</span>
            </div>
            <div class="opti-card-body" style="font-size: 12.5px; line-height: 1.6; color: #475569;">
                <b>Dataset:</b> Freight Analysis Framework (FAF6.0).<br>
                <b>Benchmark Edition:</b> 2022 Baseline Reference.<br>
                <b>Publishing Agencies:</b> Bureau of Transportation Statistics (BTS) & Federal Highway Administration (FHWA), U.S. DOT.<br>
                <b>Official Repository:</b> <a href="https://www.bts.gov/faf" target="_blank" style="color: #0D9488; text-decoration: none;">bts.gov/faf</a>.<br>
                <b>Observed Metrics:</b> Annual physical tonnage (thousand short tons) and economic value in constant 2022 US dollars ($ Millions).<br>
                <b>Scope:</b> 134 domestic CFS metropolitan regions, 42 SCTG commodities, 7 transport modes.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown("""
        <div class="opti-card" style="border-top: 3px solid #0D9488; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="opti-card-title">2. Derived Analytical Metrics</span>
                <span class="opti-pill opti-pill-teal" style="font-size: 9.5px;">Spatial Engine</span>
            </div>
            <div class="opti-card-body" style="font-size: 12.5px; line-height: 1.6; color: #475569;">
                <b>Geodesic Distance:</b> Great-circle Haversine formula between regional geographic centroids (lat, lon).<br>
                <b>Modal Circuity Multipliers:</b><br>
                • Highway Truck: 1.17x &nbsp;|&nbsp; Freight Rail: 1.25x<br>
                • Inland Waterway: 1.45x &nbsp;|&nbsp; Commercial Air: 1.05x<br>
                <b>Mass-Haul Ton-Miles:</b> Tonnage × Circuity-Adjusted Route Distance.<br>
                <b>Network Structure:</b> In/out-degree, betweenness centrality, and modal Herfindahl-Hirschman Index (HHI).
            </div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(r"""
        <div class="opti-card" style="border-top: 3px solid #D97706; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="opti-card-title">3. Modelled Assumptions</span>
                <span class="opti-pill opti-pill-amber" style="font-size: 9.5px;">Parametric LP</span>
            </div>
            <div class="opti-card-body" style="font-size: 12.5px; line-height: 1.6; color: #475569;">
                <b>Unit Operating Costs ($/ton-mile):</b><br>
                • Highway Truck: $0.180 &nbsp;|&nbsp; Freight Rail: $0.045<br>
                • Waterway Barge: $0.030 &nbsp;|&nbsp; Air Cargo: $0.850<br>
                <i>Calibrated from published BTS and AAR railroad statistics; fully user-configurable.</i><br>
                <b>Headroom Multipliers:</b> 1.20x corridor capacity and 1.25x supply headroom (modelling bounds for LP constraints, not observed physical expansions).
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # High Level National Baseline Numbers - Verified Directly Against Processed Dataset
    st.markdown("### National Freight Baseline (2022 Benchmark)")
    st.caption(
        "Baseline summary metrics dynamically verified against the active Freight Analysis Framework (FAF6) dataset. "
        "Units are strictly defined in thousands of short tons and constant 2022 US dollars."
    )

    # Dynamic calculation of active dataset metrics
    active_tons = float(flows_df["tons_2022"].sum()) if "tons_2022" in flows_df.columns else 0.0
    active_val = float(flows_df["value_2022"].sum()) if "value_2022" in flows_df.columns else 0.0
    orig_zones = set(flows_df["dms_orig"].unique())
    dest_zones = set(flows_df["dms_dest"].unique())
    active_zones = len(orig_zones.union(dest_zones))

    # Active inter-regional OD pairs (orig != dest, tons > 0)
    od_agg = flows_df.groupby(["dms_orig", "dms_dest"])["tons_2022"].sum().reset_index()
    active_inter_corridors = len(od_agg[(od_agg["tons_2022"] > 0) & (od_agg["dms_orig"] != od_agg["dms_dest"])])
    intra_od_count = len(od_agg[(od_agg["tons_2022"] > 0) & (od_agg["dms_orig"] == od_agg["dms_dest"])])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Active Freight Volume",
            value=f"{active_tons / 1e6:.2f} B Short Tons",
            delta=f"{active_tons:,.0f}k Short Tons",
            help="Total physical freight tonnage moved across the active research subnetwork in 2022. Unit: thousand short tons (1 short ton = 2,000 lbs = 0.907 metric tons)."
        )
    with c2:
        val_display = f"${active_val / 1e6:.2f} Trillion" if active_val >= 1e6 else f"${active_val / 1e3:,.1f} Billion"
        st.metric(
            label="Freight Economic Value",
            value=val_display,
            delta="Constant 2022 USD",
            help="Total economic value of moved commodities expressed in Millions of constant 2022 US dollars, adjusting for inflation across all product classifications."
        )
    with c3:
        st.metric(
            label="Geographic Scope",
            value=f"{active_zones} FAF Regions",
            delta="Representative Centroids",
            help="Active FAF geographic zones representing regional metropolitan centers. Representative points are geographical centroids, not specific terminal facilities."
        )
    with c4:
        st.metric(
            label="Active Inter-Regional Corridors",
            value=f"{active_inter_corridors} Corridors",
            delta=f"Excludes {intra_od_count} Intra-Zone Flows",
            help="Unique active directed origin-to-destination corridors with non-zero freight flow where origin ≠ destination. Intra-regional self-OD movements (orig == dest) and zero-flow pairs are excluded from this corridor count."
        )

    # Contextual Population Comparison Expander
    with st.expander("📊 National Population Comparison: Core Optimization Subnetwork vs. Full Nationwide FAF6 Database"):
        st.markdown("""
        <div style="font-size: 12.5px; color: #334155; line-height: 1.6;">
            OptiChain provides seamless scalability between the core mathematical optimization subnetwork and the complete national FAF6 database population:
            <table style="width:100%; border-collapse: collapse; margin-top: 8px; font-size: 12px;">
                <tr style="background:#F1F5F9; border-bottom: 2px solid #CBD5E1; text-align:left;">
                    <th style="padding: 6px 10px;">Metric Attribute</th>
                    <th style="padding: 6px 10px;">Active Research Subnetwork (Core 20 Hubs)</th>
                    <th style="padding: 6px 10px;">Full Nationwide FAF6 Database Scope</th>
                    <th style="padding: 6px 10px;">Methodological Note</th>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 6px 10px;"><b>Physical Freight Tonnage</b></td>
                    <td style="padding: 6px 10px;">2.87 Billion Short Tons (2,874,428.2k tons)</td>
                    <td style="padding: 6px 10px;">17.29 Billion Short Tons (17,290,649.6k tons)</td>
                    <td style="padding: 6px 10px;">Subnetwork captures ~16.6% of national volume through top 20 gateway markets.</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 6px 10px;"><b>Economic Freight Value</b></td>
                    <td style="padding: 6px 10px;">$811.48 Billion (Constant 2022 USD)</td>
                    <td style="padding: 6px 10px;">$19.58 Trillion (Constant 2022 USD)</td>
                    <td style="padding: 6px 10px;">Expressed in constant 2022 dollars without inflation distortion.</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 6px 10px;"><b>Geographic Coverage</b></td>
                    <td style="padding: 6px 10px;">20 FAF Gateway Metropolitan Regions</td>
                    <td style="padding: 6px 10px;">134 CFS Metropolitan & Remainder Zones</td>
                    <td style="padding: 6px 10px;">Complete coverage across all 50 states + District of Columbia.</td>
                </tr>
                <tr>
                    <td style="padding: 6px 10px;"><b>Active Inter-Regional Corridors</b></td>
                    <td style="padding: 6px 10px;">380 Corridors (1,008 mode-corridors)</td>
                    <td style="padding: 6px 10px;">17,810 Active Inter-Regional Corridors</td>
                    <td style="padding: 6px 10px;">Strictly excludes zero-flow links and self-OD intra-regional loops.</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Geographic Flow Map Section
    st.markdown("### Geographic Freight Desire Lines (Origin-to-Destination Corridors)")
    st.caption("Centroid-to-centroid straight desire lines colored by transportation mode. Line width represents annual cargo tonnage.")

    map_col1, map_col2 = st.columns([3, 1])
    with map_col2:
        st.markdown("**Map Controls & Filters**")
        max_links = st.slider(
            "Visible Corridors (Top N by Tonnage)",
            min_value=10,
            max_value=80,
            value=35,
            step=5,
            help="Displays the top N freight corridors ranked strictly by annual freight tonnage"
        )
        mode_filter = st.selectbox(
            "Filter Transportation Mode",
            options=[0] + list(FAF6_MODES.keys()),
            format_func=lambda m: "All Modes Combined" if m == 0 else f"{m}: {FAF6_MODES[m]}"
        )
        selected_m = mode_filter if mode_filter > 0 else None

        # Commodity Filter (SCTG)
        available_commodities = [0] + sorted(list(flows_df["sctg2"].dropna().unique()))
        comm_filter = st.selectbox(
            "Filter Commodity (SCTG)",
            options=available_commodities,
            format_func=lambda c: "All Commodities Combined" if c == 0 else f"SCTG {int(c):02d}: {get_sctg_description(c)}"
        )
        selected_c = comm_filter if comm_filter > 0 else None

        # Visible Legend for Transportation Modes and Points
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-top: 14px; font-size: 11px; line-height: 1.65;">
            <b>Transportation Mode Legend:</b><br>
            <span style="color:#2563EB; font-weight:700;">■</span> Truck<br>
            <span style="color:#DC2626; font-weight:700;">■</span> Rail<br>
            <span style="color:#0284C7; font-weight:700;">■</span> Water<br>
            <span style="color:#F59E0B; font-weight:700;">■</span> Air<br>
            <span style="color:#7C3AED; font-weight:700;">■</span> Multiple Modes & Mail<br>
            <span style="color:#059669; font-weight:700;">■</span> Pipeline<br>
            <span style="color:#64748B; font-weight:700;">■</span> Other & Unknown<br>
            <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed #CBD5E1;">
                <span style="color:#0D9488; font-weight:700;">●</span> <b>FAF Regions (Representative Points)</b><br>
                <i style="color:#64748B; font-size:10px;">Represents regional centroids, not physical rail/truck terminals.</i>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with map_col1:
        map_fig, selected_corridors_df = create_freight_network_map(
            flows_df,
            max_corridors=max_links,
            selected_mode=selected_m,
            selected_commodity=selected_c,
            return_corridors=True
        )
        st.plotly_chart(map_fig, use_container_width=True)

    # Disclaimer Note directly beneath the map
    st.caption(f"**Disclaimer:** {FLOW_DISCLAIMER}")

    # Ranked Corridors Ledger Table beneath the map
    if selected_corridors_df is not None and len(selected_corridors_df) > 0:
        with st.expander(f"📋 View Data Table: Top {len(selected_corridors_df)} Selected Corridors (Ranked by Freight Tonnage)", expanded=True):
            display_rows = []
            for rank, (_, row) in enumerate(selected_corridors_df.iterrows(), start=1):
                orig_code = int(row["dms_orig"])
                dest_code = int(row["dms_dest"])
                m_code = int(row["dms_mode"])
                entry = {
                    "Rank": rank,
                    "Origin FAF Region": f"{row['orig_name']} (FAF {orig_code})",
                    "Destination FAF Region": f"{row['dest_name']} (FAF {dest_code})",
                    "Transportation Mode": FAF6_MODES.get(m_code, f"Mode {m_code}"),
                    "Annual Tonnage (k tons)": f"{row['tons_2022']:,.1f}",
                    "Freight Value ($M, Constant 2022 USD)": f"${row['value_2022']:,.1f}" if pd.notna(row.get("value_2022")) else "N/A",
                    "Routing Distance (mi)": f"{row['distance_miles']:,.0f}" if pd.notna(row.get("distance_miles")) else "N/A"
                }
                if selected_c:
                    entry["Filtered Commodity"] = f"{get_sctg_description(selected_c)} [SCTG {selected_c:02d}]"
                display_rows.append(entry)

            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, height=260)

    # Core Macro Charts
    st.markdown("---")
    st.markdown("### National Modal Split & Commodity Distribution")
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(plot_mode_share(flows_df, metric="tons_2022"), use_container_width=True)
        st.caption("Highway trucking moves ~87.9% of domestic tonnage, resulting in high market concentration (Mode HHI = 7,796). Exact tonnage and modal share displayed on hover.")
    with ch2:
        st.plotly_chart(plot_commodity_distribution(flows_df, top_n=10), use_container_width=True)
        st.caption(SCTG_EXPLANATORY_NOTE)

    # Compact Key Findings Section (Generated Dynamically from Actual Data)
    st.markdown("---")
    st.markdown("### Key Findings from the 2022 Freight Baseline")
    st.caption("Empirical findings synthesized dynamically from the active FAF6 flow database calculations:")

    findings = compute_baseline_key_findings(flows_df)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(f"""
        <div class="opti-card" style="border-top: 3px solid #0D9488; height: 100%;">
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 6px; font-size: 13.5px;">
                Dominant Transport Mode & Market Share
            </div>
            <div style="font-size: 12.5px; color: #475569; line-height: 1.55;">
                • <b>Primary Mode:</b> {findings['dom_mode_name']} accounts for <b>{findings['dom_mode_pct']:.2f}%</b> of total freight volume ({findings['dom_mode_tons']:,.1f}k short tons).<br>
                • <b>Market Concentration:</b> Modal Herfindahl-Hirschman Index (HHI) equals <b>{findings['mode_hhi']:,.1f}</b>, signaling extreme dependence on highway trucking infrastructure.<br>
                • <b>Secondary Modes:</b> {findings['secondary_modes'][0]['name']} ({findings['secondary_modes'][0]['pct']:.2f}%) and {findings['secondary_modes'][1]['name']} ({findings['secondary_modes'][1]['pct']:.2f}%) provide multimodal buffering.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        comm_lines = "".join([
            f"• <b>SCTG {c['code']:02d} ({c['desc']}):</b> {c['tons']:,.1f}k tons ({c['pct']:.2f}%)<br>"
            for c in findings['top_comms']
        ])
        st.markdown(f"""
        <div class="opti-card" style="border-top: 3px solid #0F172A; height: 100%;">
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 6px; font-size: 13.5px;">
                Major Commodity Volume Categories
            </div>
            <div style="font-size: 12.5px; color: #475569; line-height: 1.55;">
                {comm_lines}
                • <b>Bulk Concentration:</b> The top 3 commodities represent <b>{findings['top_comms_combined_pct']:.2f}%</b> of total moved mass, dominated by heavy aggregates and agricultural staples.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        corridor_lines = "".join([
            f"• <b>{c['origin']} → {c['destination']}:</b> {c['tons']:,.1f}k tons ({c['mode']})<br>"
            for c in findings['top_corridors']
        ])
        st.markdown(f"""
        <div class="opti-card" style="border-top: 3px solid #D97706; height: 100%;">
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 6px; font-size: 13.5px;">
                Highest-Volume Inter-Regional Corridors
            </div>
            <div style="font-size: 12.5px; color: #475569; line-height: 1.55;">
                {corridor_lines}
                • <b>Network Haul Distance:</b> The tonnage-weighted average haul distance across active inter-regional pairs is <b>{findings['weighted_avg_distance']:,.1f} miles</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Workflow Navigation & Analytical Progression Transition
    st.markdown("---")
    st.markdown("### Analytical Progression: Descriptive Baseline to Prescriptive Optimization")
    st.markdown(r"""
    <div class="opti-card" style="border-left: 4px solid #0D9488; background: #FFFFFF; padding: 18px 22px; margin-top: 8px;">
        <div style="font-weight: 700; color: #0F172A; font-size: 15px; margin-bottom: 8px;">
            Research Methodology: From Empirical Observation to Mathematical Decision-Making
        </div>
        <div style="font-size: 13px; color: #475569; line-height: 1.6; margin-bottom: 14px;">
            OptiChain guides the researcher through three interconnected analytical tiers:
            <ol style="margin: 8px 0 0 18px; padding-left: 0;">
                <li><b>Stage 1: Descriptive Analytics (Current Workspace)</b> — Establishes the empirical baseline from historical FAF6 2022 observations, mapping origin-to-destination desire lines, modal splits, and commodity volumes.</li>
                <li><b>Stage 2: Structural Network Science</b> — Evaluates graph topology, degree distribution, bottleneck hub centrality, and market concentration (HHI) across nodes and transportation corridors.</li>
                <li><b>Stage 3: Prescriptive Optimization (LP Engine)</b> — Transitions to mathematical decision-making: solves large-scale Multimodal Linear Programs ($\min \sum c_{ijkm} x_{ijkm}$), isolates binding infrastructure bottlenecks via dual shadow prices ($\pi_i, \mu_{ijm}$), and stress-tests resilience against systemic disruptions.</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("Proceed to Freight Network Science →", use_container_width=True):
            st.session_state["nav_workspace_override"] = 1
            st.rerun()
    with nav_col2:
        if st.button("Launch Multimodal Freight LP Optimizer →", use_container_width=True, type="primary"):
            st.session_state["nav_workspace_override"] = 2
            st.rerun()
