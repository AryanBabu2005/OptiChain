"""
Freight Network Intelligence and Corridor Analysis UI for OptiChain.
Grounded in Network Science and Transportation Economics.
"""

from typing import Optional, Any
import streamlit as st
import pandas as pd
import numpy as np

from src.network.graph_builder import FreightGraphBuilder
from src.network.network_metrics import FreightNetworkMetrics
from src.visualization.charts import plot_top_corridors, plot_value_vs_tonnage, plot_sankey_multimodal
from src.visualization.network_plots import plot_network_topology
from src.network.geography import FAF6_DOMESTIC_ZONES, FAF6_MODES
from src.data.sctg_codes import SCTG_DESCRIPTIONS, get_sctg_description, SCTG_EXPLANATORY_NOTE

def render_freight_network(flows_df: pd.DataFrame, view_mode: str = "network"):
    """
    Render Freight Network UI:
    - 'network': Freight Network Graph Analytics, Centrality, HHI Concentration & Multimodal Sankey.
    - 'corridors': Inter-Regional Freight Corridor Density & Economic Value Ledger.
    """
    if view_mode == "corridors":
        st.header("Inter-Regional Freight Corridor Analysis")
        st.markdown(
            "An empirical examination of the highest-density freight conduits in the United States, "
            "evaluating physical freight mass (kilotons), economic density ($/ton), and transport mode allocation."
        )

        # Compute corridors distinguishing cargo economic value from carrier logistics cost
        top_corridors = FreightNetworkMetrics.compute_top_corridors(flows_df, top_n=50, include_mode=True, exclude_intra=False)

        ton_col = "tons_2022" if "tons_2022" in top_corridors.columns else "total_tons"
        val_col_name = "value_2022" if "value_2022" in top_corridors.columns else "total_value"

        # Summary Metrics
        c1, c2, c3, c4 = st.columns(4)
        total_top_tons = top_corridors[ton_col].sum() if ton_col in top_corridors.columns else 0.0
        total_top_val = top_corridors[val_col_name].sum() if val_col_name in top_corridors.columns else 0.0
        avg_density = (total_top_val * 1e6) / (total_top_tons * 1e3) if total_top_tons > 0 else 0

        with c1:
            st.metric("Analyzed Corridors", f"{len(top_corridors)}")
        with c2:
            st.metric("Top Corridors Volume", f"{total_top_tons / 1e3:,.1f} M Tons")
        with c3:
            st.metric("Top Corridors Value", f"${total_top_val / 1e3:,.1f} B")
        with c4:
            st.metric("Average Economic Density", f"${avg_density:,.0f} / ton")

        st.markdown("---")

        col_left, col_right = st.columns([3, 2])
        with col_left:
            st.subheader("Top Corridors Ranking")
            metric_to_plot = st.radio(
                "Rank Corridors By:",
                ["Volume (Thousand Tons)", "Economic Cargo Value (Million $)"],
                horizontal=True
            )
            plot_val_col = ton_col if "Volume" in metric_to_plot else val_col_name
            st.plotly_chart(plot_top_corridors(top_corridors, top_n=10, value_col=plot_val_col), use_container_width=True)

        with col_right:
            st.markdown("""
            <div class="opti-card" style="border-left: 4px solid #0D9488; height: 100%; padding: 16px; background-color: #F8FAFC; border-radius: 6px;">
                <div style="font-weight: 700; color: #0F172A; margin-bottom: 8px; font-size: 14px;">
                    Corridor Economics & Density Dynamics
                </div>
                <div style="font-size: 12.5px; color: #475569; line-height: 1.55;">
                    <b>Volume-Heavy Bulk Corridors:</b><br>
                    Intrastate industrial routes (Texas Gulf Coast, California Central Valley) dominate physical mass, moving low-value raw materials (gravel, petroleum, cement, animal feed). These depend heavily on barge, rail, and heavy trucking.<br><br>
                    <b>Value-Heavy Consumer Conduits:</b><br>
                    Cross-country corridors (Los Angeles to Chicago, New York to Atlanta) exhibit high <b>economic value density</b> ($/ton), moving finished electronics, medical equipment, and consumer goods via expedited trucking.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Detailed Corridor Volume & Value Ledger")

        # Crucial Economics Callout
        st.info(
            "💡 **Transportation Economics Distinction: Cargo Freight Value vs. Carrier Logistics Cost**\n\n"
            "• **Cargo Freight Value ($ Millions):** The commercial/market economic worth of the physical commodities inside the shipment (reported directly in official FAF6 statistics).\n"
            "• **Carrier Transport Cost ($ Millions):** The operational expense paid to freight carriers to haul the tonnage across the corridor ($ = \\text{Tons} \\times \\text{Miles} \\times \\text{Ton-Mile Rate}$). Typically 2% to 15% of cargo value depending on commodity density and distance."
        )

        filter_c1, filter_c2 = st.columns([2, 1])
        with filter_c1:
            search_query = st.text_input("Filter Corridors by Region Name (e.g. 'Chicago', 'Dallas', 'Los Angeles'):", "")
        with filter_c2:
            corridor_type_filter = st.selectbox(
                "Corridor Scope:",
                ["All Corridors (Including Intra-Regional)", "Inter-Regional Corridors Only (Exclude Self-Loops)"]
            )

        display_df = top_corridors.copy()
        if "Inter-Regional" in corridor_type_filter:
            display_df = display_df[display_df["dms_orig"] != display_df["dms_dest"]]

        if search_query:
            display_df = display_df[
                display_df["orig_name"].str.contains(search_query, case=False, na=False) |
                display_df["dest_name"].str.contains(search_query, case=False, na=False)
            ]

        # Ensure value density exists
        if "value_per_ton" not in display_df.columns:
            display_df["value_per_ton"] = np.where(
                display_df[ton_col] > 0,
                (display_df[val_col_name] * 1000.0) / display_df[ton_col],
                0.0
            )

        cols_to_show = [
            "orig_name", "dest_name", "mode_name", ton_col, val_col_name,
            "value_per_ton", "distance_miles", "thousand_ton_miles", "carrier_transport_cost_mil"
        ]
        col_rename_map = {
            "orig_name": "Origin Region",
            "dest_name": "Destination Region",
            "mode_name": "Transport Mode",
            ton_col: "Freight Tonnage (k tons)",
            val_col_name: "Cargo Value ($M)",
            "value_per_ton": "Value Density ($/ton)",
            "distance_miles": "Distance (mi)",
            "thousand_ton_miles": "Ton-Miles (k ton-mi)",
            "carrier_transport_cost_mil": "Carrier Transport Cost ($M)"
        }
        present_cols = [c for c in cols_to_show if c in display_df.columns]
        table_df = display_df[present_cols].rename(columns=col_rename_map)

        st.dataframe(table_df, use_container_width=True, height=340)

        st.markdown("---")
        st.subheader("Freight Value vs Physical Tonnage Trade-off")
        st.markdown(
            "Scatter plot of freight records comparing physical weight (thousands of tons) against economic cargo value (millions of dollars). "
            "High slope indicates premium, high-value freight; low slope represents bulk raw materials."
        )
        st.plotly_chart(plot_value_vs_tonnage(flows_df), use_container_width=True)

    else:
        # Network Science & Graph Analytics View
        st.header("Freight Network Graph Analytics & Market Concentration")
        st.markdown(
            "Topological analysis of the national freight movement network using **NetworkX**. "
            "Evaluates connectivity, central gateway nodes, and modal concentration using the **Herfindahl-Hirschman Index (HHI)**."
        )

        # 1. Build NetworkX graph excluding self-loops for inter-regional topology
        G = FreightGraphBuilder.build_graph_from_flows(flows_df, exclude_self_loops=True)
        node_df = FreightNetworkMetrics.compute_node_metrics(G)
        hhi = FreightNetworkMetrics.compute_concentration_indices(flows_df)

        g_meta = G.graph
        total_regions = g_meta.get("total_regions", G.number_of_nodes())
        active_corridors = g_meta.get("active_directed_corridors", G.number_of_edges())
        total_combos = g_meta.get("total_corridor_combinations", total_regions * total_regions)
        intra_zones = g_meta.get("intra_regional_zones", 20)
        zero_flow_corrs = g_meta.get("zero_flow_corridors", 0)

        # 2. Executive Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(
                "Active FAF Regions",
                f"{total_regions} FAF Regions",
                delta="Representative Points",
                help="The 20 major domestic gateway regions representing metropolitan anchor centroids and state remainder zones."
            )
            st.caption("Domestic FAF6 regional gateway zones.")

        with c2:
            st.metric(
                "Active Directed Corridors",
                f"{active_corridors} Corridors",
                delta=f"Active Inter-Regional (u ≠ v)",
                help=f"Out of {total_combos} total OD combinations ({total_regions}×{total_regions}): {active_corridors} active inter-regional corridors, {intra_zones} local intra-regional zones, {zero_flow_corrs} zero-flow corridors."
            )
            st.caption(f"{active_corridors} active inter-regional conduits (out of {total_combos} combinations).")

        with c3:
            st.metric(
                "Mode HHI Concentration",
                f"{hhi['mode_hhi']:,.1f}",
                delta=f"{hhi['mode_concentration_level']} (> 2,500 Threshold)",
                help="Herfindahl-Hirschman Index: HHI = Σ (s_i)^2. Shares are based on physical freight tonnage. Values > 2,500 indicate high concentration."
            )
            st.caption("Severe truck dominance (87.9% tonnage) leaves supply chains vulnerable to fuel and driver shocks.")

        with c4:
            st.metric(
                "Commodity HHI Concentration",
                f"{hhi['commodity_hhi']:,.1f}",
                delta=f"{hhi['commodity_concentration_level']} (< 1,500 Threshold)",
                help="Herfindahl-Hirschman Index: HHI = Σ (s_i)^2 on physical tonnage. Values < 1,500 indicate healthy diversification."
            )
            st.caption("Well-balanced freight mix across gravel, mineral products, agriculture, and foodstuffs.")

        st.markdown("---")

        # 3. HHI Explanation & Underlying Share Tables
        st.subheader("Herfindahl-Hirschman Index (HHI) Market Concentration Analysis")
        st.markdown(
            """
            The **Herfindahl-Hirschman Index (HHI)** is a standard quantitative metric of operational and economic concentration. 
            In OptiChain, it is calculated by squaring the percentage share ($s_i$, from 0 to 100) of each category and summing the squares:
            $$\\text{HHI} = \\sum_{i=1}^{n} s_i^2$$
            where $\\sum s_i = 100$. An HHI near 0 reflects complete diversification, while 10,000 represents a pure single-category monopoly ($100^2 = 10,000$).
            """
        )

        hhi_basis = st.radio(
            "Select HHI Analysis Basis:",
            ["Physical Freight Tonnage (Thousand Short Tons) — Primary Logistics Basis",
             "Cargo Economic Value ($ Millions) — Cargo Value Density Basis"],
            horizontal=True
        )

        is_tonnage_basis = "Tonnage" in hhi_basis

        # Summary of HHI values on selected basis
        active_mode_hhi = hhi["mode_hhi"] if is_tonnage_basis else hhi.get("mode_hhi_value", hhi["mode_hhi"])
        active_comm_hhi = hhi["commodity_hhi"] if is_tonnage_basis else hhi.get("commodity_hhi_value", hhi["commodity_hhi"])
        basis_label = "Freight Tonnage" if is_tonnage_basis else "Cargo Economic Value"

        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border-left: 4px solid #0D9488; padding: 12px 16px; border-radius: 6px; margin: 10px 0 16px 0;">
                <span style="font-weight: 700; color: #0F172A; font-size: 13.5px;">
                    Current Evaluation Basis: {basis_label}
                </span><br>
                <span style="font-size: 12.5px; color: #475569;">
                    • <b>Mode HHI:</b> <b>{active_mode_hhi:,.2f}</b> ({"High Concentration" if active_mode_hhi > 2500 else "Moderate Concentration"}) — Highway trucking accounts for >87% of the national freight flow.<br>
                    • <b>Commodity HHI:</b> <b>{active_comm_hhi:,.2f}</b> ({"Unconcentrated / Diversified" if active_comm_hhi < 1500 else ("Moderate Concentration" if active_comm_hhi <= 2500 else "High Concentration")}) — Physical mass is diversified across heavy bulk materials and consumer consumables.
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Expandable Underlying Share Tables
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            with st.expander("📊 View Underlying Transport Mode Market Shares & HHI Squared Terms", expanded=False):
                mode_df = hhi["mode_shares_df"].copy()
                if not mode_df.empty:
                    display_mode_df = pd.DataFrame({
                        "Mode Code": mode_df["dms_mode"],
                        "Transportation Mode": mode_df["mode_name"],
                        "Tonnage (k tons)": mode_df["tons_2022"].apply(lambda v: f"{v:,.1f}"),
                        "Tonnage Share (%)": mode_df["share_tons_pct"].apply(lambda v: f"{v:.2f}%"),
                        "Squared Tonnage Share (s_i²)": mode_df["squared_share_tons"].apply(lambda v: f"{v:,.2f}"),
                        "Value ($M)": mode_df["value_2022"].apply(lambda v: f"${v:,.1f}"),
                        "Value Share (%)": mode_df["share_val_pct"].apply(lambda v: f"{v:.2f}%"),
                        "Squared Value Share (s_v²)": mode_df["squared_share_val"].apply(lambda v: f"{v:,.2f}")
                    })
                    st.dataframe(display_mode_df, use_container_width=True, hide_index=True)
                    st.caption(f"Sum of Squared Tonnage Shares = {hhi['mode_hhi']:,.2f} | Sum of Squared Value Shares = {hhi.get('mode_hhi_value', 0.0):,.2f}")

        with exp_col2:
            with st.expander("📊 View Underlying Commodity Market Shares & HHI Squared Terms (SCTG2)", expanded=False):
                comm_df = hhi["commodity_shares_df"].copy()
                if not comm_df.empty:
                    display_comm_df = pd.DataFrame({
                        "SCTG Code": comm_df["sctg2"],
                        "Commodity Description": comm_df["commodity_name"],
                        "Tonnage (k tons)": comm_df["tons_2022"].apply(lambda v: f"{v:,.1f}"),
                        "Tonnage Share (%)": comm_df["share_tons_pct"].apply(lambda v: f"{v:.2f}%"),
                        "Squared Share (s_i²)": comm_df["squared_share_tons"].apply(lambda v: f"{v:,.2f}"),
                        "Value ($M)": comm_df["value_2022"].apply(lambda v: f"${v:,.1f}"),
                        "Value Share (%)": comm_df["share_val_pct"].apply(lambda v: f"{v:.2f}%")
                    })
                    st.dataframe(display_comm_df, use_container_width=True, hide_index=True, height=280)
                    st.caption(f"Sum of Squared Tonnage Shares = {hhi['commodity_hhi']:,.2f} | Sum of Squared Value Shares = {hhi.get('commodity_hhi_value', 0.0):,.2f}")

        st.markdown("---")

        # 4. Topology Graph & Multimodal Sankey Rows
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Network Topology Graph")
            st.caption("Visualizing gateway connectivity between FAF regions. Node size represents throughput; edge width indicates corridor volume.")
            
            top_controls_c1, top_controls_c2 = st.columns([2, 3])
            with top_controls_c1:
                layout = st.selectbox("Graph Layout Algorithm", ["spring", "circular", "kamada_kawai"], key="net_layout_sel")
            with top_controls_c2:
                st.caption("ℹ️ **Spring layout** is a force-directed visual clustering algorithm, not an optimal routing path.")

            st.plotly_chart(plot_network_topology(G, layout_type=layout), use_container_width=True)

        with col2:
            st.subheader("Multimodal Flow Allocation (Sankey)")
            st.caption("Flow allocation from Origins → Transportation Modes → Destinations (Conserved flow without double-counting).")

            sankey_c1, sankey_c2 = st.columns(2)
            with sankey_c1:
                # Build Commodity choices from dataset
                comm_codes_present = sorted(list(flows_df["sctg2"].unique()))
                comm_options = ["All Commodities"] + [f"{c:02d}: {get_sctg_description(c)}" for c in comm_codes_present]
                sel_comm_str = st.selectbox("Filter Commodity:", comm_options, key="sankey_comm_filter")
                if sel_comm_str == "All Commodities":
                    selected_commodity_code = None
                else:
                    selected_commodity_code = int(sel_comm_str.split(":")[0])

            with sankey_c2:
                # Build Mode choices
                modes_present = sorted(list(flows_df["dms_mode"].unique()))
                mode_options = ["All Modes"] + [f"{m}: {FAF6_MODES.get(m, f'Mode {m}')}" for m in modes_present]
                sel_mode_str = st.selectbox("Filter Transportation Mode:", mode_options, key="sankey_mode_filter")
                if sel_mode_str == "All Modes":
                    selected_mode_code = None
                else:
                    selected_mode_code = int(sel_mode_str.split(":")[0])

            st.plotly_chart(
                plot_sankey_multimodal(
                    flows_df,
                    max_links=25,
                    selected_commodity=selected_commodity_code,
                    selected_mode=selected_mode_code
                ),
                use_container_width=True
            )
            st.caption("⚖️ **Kirchhoff Mass Conservation:** Total mass entering each transport mode from origins exactly equals total mass departing to destinations.")

        st.markdown("---")

        # 5. Corridor Volume & Value Rankings
        st.subheader("Highest-Volume & Highest-Value Corridor Rankings")
        st.markdown(
            "Empirical examination of the top national freight corridors, contrasting **cargo freight economic value** "
            "against **carrier logistics transportation cost**."
        )

        rank_c1, rank_c2, rank_c3 = st.columns([2, 2, 2])
        with rank_c1:
            rank_metric = st.radio(
                "Rank Corridors By:",
                ["Volume (Thousand Tons)", "Cargo Value ($ Millions)"],
                horizontal=True,
                key="corr_rank_metric"
            )
        with rank_c2:
            include_intra_opt = st.checkbox("Include Intra-Regional Flows (u = v)", value=False, key="rank_intra_opt")
        with rank_c3:
            top_n_slider = st.slider("Number of Top Corridors:", min_value=5, max_value=30, value=15, step=5, key="rank_n_slider")

        corridors_ranked = FreightNetworkMetrics.compute_top_corridors(
            flows_df,
            top_n=100,
            include_mode=True,
            exclude_intra=(not include_intra_opt)
        )

        sort_col = "tons_2022" if "Volume" in rank_metric else "value_2022"
        top_ranked_df = corridors_ranked.sort_values(by=sort_col, ascending=False).head(top_n_slider).reset_index(drop=True)

        # Presentation columns
        rank_table = pd.DataFrame({
            "Rank": range(1, len(top_ranked_df) + 1),
            "Origin FAF Region": top_ranked_df["orig_name"],
            "Destination FAF Region": top_ranked_df["dest_name"],
            "Transport Mode": top_ranked_df["mode_name"],
            "Freight Tonnage (k tons)": top_ranked_df["tons_2022"].apply(lambda v: f"{v:,.1f}"),
            "Cargo Economic Value ($M)": top_ranked_df["value_2022"].apply(lambda v: f"${v:,.1f}"),
            "Cargo Value Density ($/ton)": top_ranked_df["value_per_ton"].apply(lambda v: f"${v:,.0f}"),
            "Distance (mi)": top_ranked_df["distance_miles"].apply(lambda v: f"{v:,.0f}"),
            "Carrier Transport Cost ($M)": top_ranked_df["carrier_transport_cost_mil"].apply(lambda v: f"${v:,.2f}")
        })

        st.dataframe(rank_table, use_container_width=True, hide_index=True)

        st.caption(
            "💡 **Economic Note:** Cargo Economic Value is the total market worth of goods in transit. "
            "Carrier Transport Cost is the carrier hauling expense ($ = \\text{tons} \\times \\text{distance} \\times \\text{mode rate/ton-mile}$). "
            "High value-density corridors indicate high-tech manufacturing, while low density signifies bulk raw materials."
        )

        st.markdown("---")

        # 6. Regional Hub Centrality & Criticality Ledger
        st.subheader("FAF Regional Gateway Centrality Ledger")
        st.markdown("""
        **Topological Centrality in Freight Logistics:**
        - **Inflow / Outflow Throughput:** Total physical mass (thousand short tons) entering or departing the regional centroid.
        - **Betweenness Centrality ($C_B$):** Measures the proportion of shortest freight paths passing through the region. Nodes with high betweenness (e.g. Chicago, Dallas) act as critical national transshipment bridges; disruptions here cascade across the national network.
        - **PageRank:** Reflects systemic structural prestige — a region achieves high PageRank when it directly exchanges substantial freight volume with other high-capacity logistics gateways.
        """)

        # Clean display of node_df
        display_nodes = node_df.copy()
        display_nodes_table = pd.DataFrame({
            "FAF Zone": display_nodes["zone_code"],
            "Region Name": display_nodes["name"],
            "State": display_nodes["state"],
            "Inflow (k tons)": display_nodes["inflow_tons"].apply(lambda v: f"{v:,.1f}"),
            "Outflow (k tons)": display_nodes["outflow_tons"].apply(lambda v: f"{v:,.1f}"),
            "Intra-Regional (k tons)": display_nodes["intra_regional_tons"].apply(lambda v: f"{v:,.1f}"),
            "Total Throughput (k tons)": display_nodes["total_throughput_tons"].apply(lambda v: f"{v:,.1f}"),
            "In-Degree": display_nodes["in_degree"],
            "Out-Degree": display_nodes["out_degree"],
            "Betweenness Centrality": display_nodes["betweenness_centrality"].apply(lambda v: f"{v:.5f}"),
            "PageRank Prestige": display_nodes["pagerank"].apply(lambda v: f"{v:.5f}")
        })

        st.dataframe(display_nodes_table, use_container_width=True, hide_index=True, height=350)

        st.markdown("---")

        # 7. Theoretical Foundations & Mathematical Reference
        st.subheader("Theoretical Foundations & Mathematical Reference")
        st.caption("Mathematical formulations, network science theorems, and economic principles underpinning OptiChain's multimodal freight analytics.")

        with st.expander("📐 Theoretical Framework 1: Graph Theory & Spatial Network Formalization"):
            st.markdown(r"""
            **1. Formal Network Definition:**
            The national freight flow network is formalized as a directed weighted multigraph $G = (V, E, W)$:
            - **Vertices $V$:** The 20 FAF6 domestic regional gateway zones ($|V| = 20$), representing major metropolitan anchor centroids and state remainder zones.
            - **Edges $E$:** Directed freight conduits $(u, v) \in E$ transporting commodities between origin $u$ and destination $v$.
            - **Weights $W$:** Physical freight mass $T_{uv}$ (thousand short tons) and cargo economic worth $V_{uv}$ (\$ millions).

            **2. Inter-Regional vs. Intra-Regional Flows:**
            - **Active Directed Corridors ($u \neq v$):** There are exactly 380 active directed inter-regional conduits in the gateway subnetwork, with zero zero-flow corridors.
            - **Intra-Regional Flow ($u = v$):** Freight moving within the same regional centroid boundary (e.g. Phoenix to Phoenix). In FAF6, intra-regional freight accounts for over 85% of total tonnage due to local distribution of heavy bulk materials (gravel, stone, asphalt). These are tracked as node self-throughput attributes rather than topological inter-regional edges.

            **3. Topological Layouts vs. Physical Routing:**
            - The **Spring Layout** (Fruchterman-Reingold force-directed algorithm) treats edges as springs governed by Hooke's Law and nodes as repulsive particles. It clusters tightly interconnected logistics regions together topologically.
            - *Methodological Note:* The force-directed spring layout serves as a topological connectivity abstraction; it clusters tightly interconnected logistics regions together topologically rather than representing geographical highway coordinates or physical infrastructure geometry.
            """)

        with st.expander("📐 Theoretical Framework 2: Network Centrality & Structural Vulnerability Dynamics"):
            st.markdown(r"""
            **1. Degree Metrics:**
            - **In-Degree $k_v^{in}$ & Out-Degree $k_v^{out}$:** Number of unique origin and destination regions connected to node $v$.
            - **Weighted In/Out Degree:** Total physical cargo mass entering ($\sum_{u} W_{uv}$) or exiting ($\sum_{w} W_{vw}$) the region.

            **2. Betweenness Centrality ($C_B$):**
            $$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
            where $\sigma_{st}$ is the total number of shortest (lowest impedance) logistics paths from node $s$ to node $t$, and $\sigma_{st}(v)$ is the number of those paths passing through gateway $v$.
            - *Physical Interpretation:* Regions with high betweenness (such as Chicago, Dallas-Fort Worth, and Memphis) act as **critical national transshipment bottlenecks**. A disruption (e.g. weather event, bridge collapse, or terminal strike) at a high-betweenness node triggers cascading delays across multiple downstream supply chains.

            **3. PageRank Prestige ($PR$):**
            $$PR(u) = \frac{1 - d}{|V|} + d \sum_{v \in M(u)} \frac{PR(v)}{L(v)}$$
            where $d = 0.85$ is the damping factor, $M(u)$ is the set of nodes delivering freight to $u$, and $L(v)$ is the out-degree of $v$.
            - *Physical Interpretation:* PageRank measures structural systemic authority. A regional gateway receives high PageRank not merely because of high local volume, but because it is directly coupled with other high-capacity logistics gateways.
            """)

        with st.expander("📐 Economic Methodology 3: Herfindahl-Hirschman Market Concentration Theory"):
            st.markdown(r"""
            **1. Mathematical Formulation:**
            $$\text{HHI} = \sum_{i=1}^{n} s_i^2$$
            where $s_i = \left(\frac{x_i}{\sum_{k=1}^n x_k}\right) \times 100$ represents the percentage share of category $i$ ($0 \le s_i \le 100$).
            
            **2. Why Squaring Matters in Transportation Economics:**
            Squaring percentage shares gives exponentially higher weight to dominant modes. 
            - For an evenly split 5-mode system ($20\%$ each): $\text{HHI} = 5 \times (20^2) = 2,000$.
            - For the actual US freight system, where highway trucking holds $87.92\%$: $87.92^2 = 7,729.9$, propelling overall Mode HHI to **7,795.97**.

            **3. US DOJ / FTC Regulatory Benchmarks:**
            - **$\text{HHI} < 1,500$ (Unconcentrated / Diversified):** Highly competitive and resilient against single-mode failure.
            - **$1,500 \le \text{HHI} \le 2,500$ (Moderately Concentrated):** Moderate market power or operational reliance.
            - **$\text{HHI} > 2,500$ (Highly Concentrated):** Severe single-point failure risk and lack of multimodal redundancy.

            **4. Physical Tonnage vs. Cargo Economic Value:**
            - **Mode HHI on Tonnage (~7,796):** Physical movement is overwhelmingly dominated by highway trucking (87.9% tons), meaning the nation's physical supply chain is acutely vulnerable to diesel price spikes, driver shortages, and interstate highway closures.
            - **Commodity HHI on Tonnage (~1,455):** Tonnage is unconcentrated and diversified because heavy bulk construction aggregates (gravel: 23.3%, minerals: 22.2%) balance agricultural grains (12.0%) and refined fuels (8.2%).
            """)

        with st.expander("📐 Conservation Principles 4: Sankey Multimodal Flow Allocation & Kirchhoff Conservation"):
            st.markdown(r"""
            **1. Multimodal Layered Flow Model:**
            The Sankey diagram models freight transshipment through a 3-layer bipartite transition:
            $$\text{Origin Regions } (O_i) \longrightarrow \text{Transportation Modes } (M_k) \longrightarrow \text{Destination Regions } (D_j)$$

            **2. Kirchhoff Mass Conservation:**
            At every transportation mode node $M_k$, the incoming freight volume from all origin regions strictly equals the outgoing freight volume to all destination regions:
            $$\sum_{i} \text{Flow}(O_i \to M_k) = \sum_{j} \text{Flow}(M_k \to D_j) = \sum_{r \in \text{Records}, \text{mode}(r)=k} \text{Tonnage}(r)$$
            This mathematical guarantee ensures that no phantom freight mass is artificially generated or lost during visual aggregation.

            **3. Multimodal Policy Application:**
            Transportation planners and logistics engineers use this visualization to detect **modal shift opportunities** (e.g. evaluating what fraction of long-haul highway trucking flows between California and the Midwest could be shifted to lower-emission Class I rail intermodal corridors).
            """)
