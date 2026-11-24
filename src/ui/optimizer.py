"""
Multimodal Freight Optimizer & Capacity Planning UI for OptiChain.
Solves the central multicommodity freight allocation linear program and evaluates
infrastructure capacity bottlenecks using dual shadow prices.
"""

from typing import Optional, Any
import streamlit as st
import pandas as pd
import numpy as np

from src.models.freight_model import MultimodalFreightModel
from src.models.capacity_model import CapacityPlanningModel
from src.database.storage import OptiChainDatabase
from src.data.sctg_codes import get_sctg_description
from src.network.geography import FAF6_MODES

def render_optimizer_ui(flows_df: pd.DataFrame, view_mode: str = "optimizer"):
    """
    Render Multimodal Freight Flow Optimizer UI:
    - 'optimizer': Linear Programming Multicommodity Flow Allocation with dual shadow prices.
    - 'capacity': Capital Capacity Expansion & Bottleneck Investment Planning.
    """
    db = OptiChainDatabase()

    if view_mode == "capacity":
        st.header("Capacity Bottlenecks & Dual Shadow Price Valuation")
        st.markdown(
            "Evaluation of network infrastructure bottlenecks where physical capacity limits are active. "
            "Leverages **linear programming dual variables (shadow prices)** to identify corridors where "
            "capital expansion produces the highest marginal logistics cost savings."
        )

        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0D9488; padding: 14px 18px; border-radius: 6px; margin-bottom: 16px;">
            <div style="font-weight: 700; color: #0F172A; margin-bottom: 6px; font-size: 14px;">
                Economic Principle of Linear Programming Dual Shadow Prices:
            </div>
            <div style="font-size: 13px; color: #475569; line-height: 1.55;">
                When a freight corridor's capacity constraint is binding, expanding throughput capacity 
                by one short ton decreases total national logistics cost by exactly the <b>dual shadow price</b>:
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.latex(r"\pi_{i,j,m} = -\frac{\partial Z^*}{\partial u_{i,j,m}} \ge 0")

        st.caption(
            "If a corridor's shadow price exceeds its annualized unit capital expansion cost, expanding capacity is financially justified "
            "because recurring annual logistics savings surpass capital construction and financing expenses."
        )

        with st.expander("Capacity Expansion Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                cap_factor = st.slider(
                    "Current Route Capacity Factor", 0.8, 1.5, 1.0, 0.05,
                    help="1.0 = capacity equals observed flows; values < 1.0 simulate tightening"
                )
            with col2:
                max_exp = st.slider("Max Expansion Cap per Corridor (k tons)", 100.0, 2000.0, 800.0, 100.0)

        if st.button("Run Joint Capacity & Flow Optimization", type="primary"):
            with st.spinner("Solving joint flow and expansion LP..."):
                cap_model = CapacityPlanningModel()
                cap_res = cap_model.plan_capacity(flows_df, base_capacity_factor=cap_factor, max_expansion_allowed=max_exp)

            if cap_res["status"] == "optimal":
                st.success("Optimization complete! Optimal expansion plan found.")
                k1, k2, k3 = st.columns(3)
                with k1:
                    st.metric("Total System Cost", f"${cap_res['total_objective']:,.2f}")
                with k2:
                    st.metric("Freight Operating Cost", f"${cap_res['transportation_cost']:,.2f}")
                with k3:
                    st.metric("Capital Investment Cost", f"${cap_res['capacity_expansion_cost']:,.2f}")

                st.subheader(f"Recommended Expansion Corridors ({cap_res['num_expanded_corridors']} Corridors Justified)")
                st.caption("These corridors have shadow prices high enough to justify capital expansion expenditure:")
                rec_df = cap_res["recommended_expansions_df"]
                st.dataframe(rec_df, use_container_width=True)
            else:
                st.error(f"Solver Error: {cap_res.get('message', 'Infeasible')}")

    else:
        # Standard Optimizer View
        st.header("Multimodal Freight Flow Optimizer (Linear Programming)")
        st.markdown(
            "Cost-minimization multicommodity freight network allocation using **SciPy HiGHS**. "
            "Optimizes modal split across highway, rail, and waterway corridors under physical demand, supply, and capacity constraints."
        )

        # 1. Mathematical Formulation & Equation Rendering
        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0D9488; padding: 14px 18px; border-radius: 6px; margin-bottom: 14px;">
            <div style="font-weight: 700; color: #0F172A; font-size: 14px; margin-bottom: 4px;">
                Mathematical Formulation: Multicommodity Multimodal Freight Allocation
            </div>
            <div style="font-size: 12.5px; color: #475569; line-height: 1.5;">
                The linear programming model determines optimal continuous freight flows <i>x</i><sub>i,j,k,m</sub> across origins, destinations, commodities, and modes to minimize aggregate logistics transportation cost.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Objective Function: Total Logistics Cost Minimization**")
        st.latex(r"\min Z = \sum_{i \in \mathcal{O}} \sum_{j \in \mathcal{D}} \sum_{k \in \mathcal{K}} \sum_{m \in \mathcal{M}} c_{i,j,m} \cdot x_{i,j,k,m}")
        st.caption(
            "Minimizes the aggregate national logistics freight transportation expenditure, where "
            r"$c_{i,j,m} = \text{rate}_m \times \text{distance}_{i,j}$ ($\$ / \text{ton}$) is the unit transportation cost "
            r"and $x_{i,j,k,m}$ is the decision variable representing allocated freight volume (thousand short tons)."
        )

        st.markdown("---")
        st.markdown("**System Constraints & Operational Descriptions:**")

        # Constraint 1: Demand Conservation
        st.latex(r"\sum_{m \in \mathcal{M}} x_{i,j,k,m} = d_{i,j,k} \quad \forall (i, j) \in \mathcal{C}, \forall k \in \mathcal{K}")
        st.markdown(
            "**• Destination Demand Conservation:** "
            r"Guarantees that the physical freight demand $d_{i,j,k}$ for commodity $k$ between origin region $i$ and destination region $j$ "
            "is fully delivered across the available transportation modes. Total inflow to destination $j$ must exactly satisfy regional consumption requirements; "
            "no unsatisfied demand, stockouts, or phantom shipments are permitted."
        )

        # Constraint 2: Origin Regional Supply Limits
        st.latex(r"\sum_{j \in \mathcal{D}} \sum_{m \in \mathcal{M}} x_{i,j,k,m} \le S_{i,k} \quad \forall i \in \mathcal{O}, \forall k \in \mathcal{K}")
        st.markdown(
            "**• Origin Regional Supply Limits:** "
            r"Enforces that the aggregate tonnage of commodity $k$ dispatched from origin region $i$ to all domestic destinations "
            r"does not exceed that region's physical production capacity or outbound commodity supply availability $S_{i,k}$. "
            "Prevents regions from dispatching more physical inventory than their local manufacturing, mining, or agricultural base generates."
        )

        # Constraint 3: Corridor-Mode Capacity Bounds
        st.latex(r"\sum_{k \in \mathcal{K}} x_{i,j,k,m} \le u_{i,j,m} \quad \forall (i, j) \in \mathcal{C}, \forall m \in \mathcal{M}")
        st.markdown(
            "**• Corridor-Mode Capacity Bounds:** "
            r"Caps the aggregate tonnage of all transported commodities sharing physical corridor $(i, j)$ via mode $m$ at the maximum throughput capacity $u_{i,j,m}$. "
            "Reflects infrastructure physical limits, including interstate highway vehicle throughput, Class I railway block-train slot availability, "
            "and inland waterway lock-and-dam barge tow draft capacities."
        )

        # Constraint 4: Non-Negativity Constraints
        st.latex(r"x_{i,j,k,m} \ge 0 \quad \forall i \in \mathcal{O}, \forall j \in \mathcal{D}, \forall k \in \mathcal{K}, \forall m \in \mathcal{M}")
        st.markdown(
            "**• Non-Negativity Constraints:** "
            "Enforces physical reality: freight mass cannot be negative (cargo moves unidirectionally from shippers to receivers). "
            "This continuous linear formulation defines a convex feasible polyhedron, guaranteeing polynomial-time solvability to global optimality via the Simplex or Interior-Point methods."
        )

        st.markdown("---")

        # 2. Consistent Dimensional Units Callout
        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px;">
            <span style="font-weight: 700; color: #0F172A; font-size: 13px;">
                📐 Consistent Dimensional Units Reference:
            </span><br>
            <span style="font-size: 12px; color: #475569; line-height: 1.5;">
                • <b>Freight Flows & Demands:</b> Thousand Short Tons (<i>k tons</i> = 1,000 tons)<br>
                • <b>Corridor Distances:</b> Statute Miles (<i>mi</i>)<br>
                • <b>Mode Freight Rates:</b> Dollars per Ton-Mile ($ / ton-mile)<br>
                • <b>Unit Logistics Cost:</b> Dollars per Short Ton ($ / ton = rate × distance)<br>
                • <b>Total Cost Objective Value:</b> Thousand Dollars ($k USD; total system cost equals <i>Z × 1,000</i> USD).
            </span>
        </div>
        """, unsafe_allow_html=True)

        # 3. Parameters, Headroom Tooltip, and Reset to Baseline
        if "opt_cap_mult" not in st.session_state:
            st.session_state["opt_cap_mult"] = 1.25
        if "opt_sup_factor" not in st.session_state:
            st.session_state["opt_sup_factor"] = 1.25

        with st.expander("Optimizer Parameters & Sensitivity Settings", expanded=True):
            st.info(
                "ℹ️ **Parametric Modeling Assumptions (Headroom Multipliers):**\n\n"
                "The two multipliers below are theoretical scenario parameters used for linear programming sensitivity analysis:\n"
                "• **Corridor Capacity Headroom:** Multiplies observed 2022 freight volume by factor $\\mu_{\\text{cap}}$ to simulate available physical throughput headroom.\n"
                "• **Origin Supply Headroom:** Multiplies observed regional production by factor $\\mu_{\\text{sup}}$ to simulate factory and agricultural supply elasticity.\n\n"
                "**Important:** These multipliers modify base modeling assumptions to evaluate network flexibility; they do **not** represent observed real-world infrastructure expansions. "
                "Setting both multipliers to **1.00x** strictly enforces observed 2022 baseline flow limits."
            )

            param_col1, param_col2 = st.columns(2)
            with param_col1:
                cap_mult = st.slider(
                    "Corridor Capacity Headroom Multiplier (μ_cap)",
                    min_value=0.80, max_value=2.00,
                    value=float(st.session_state["opt_cap_mult"]),
                    step=0.05,
                    help="Multiplies observed 2022 corridor volume by factor μ_cap to simulate route capacity bounds. Modifies base modeling assumptions; not an observed real-world expansion.",
                    key="slider_cap_mult"
                )
                st.session_state["opt_cap_mult"] = cap_mult

            with param_col2:
                sup_factor = st.slider(
                    "Origin Supply Headroom Factor (μ_sup)",
                    min_value=0.80, max_value=2.00,
                    value=float(st.session_state["opt_sup_factor"]),
                    step=0.05,
                    help="Multiplies observed regional production by factor μ_sup to simulate local inventory availability. Modifies base modeling assumptions; not an observed real-world factory expansion.",
                    key="slider_sup_factor"
                )
                st.session_state["opt_sup_factor"] = sup_factor

            btn_c1, btn_c2 = st.columns([1, 3])
            with btn_c1:
                if st.button("↺ Reset to Baseline (1.00x)", help="Restores both capacity and supply headroom multipliers to historical 1.00x baseline"):
                    st.session_state["opt_cap_mult"] = 1.00
                    st.session_state["opt_sup_factor"] = 1.00
                    st.rerun()

        # Run Optimization Button
        if st.button("Run Multimodal Optimization", type="primary"):
            with st.spinner("Formulating multicommodity LP and solving via SciPy HiGHS Dual Simplex..."):
                model = MultimodalFreightModel()
                sol = model.build_and_solve(
                    flows_df,
                    capacity_multiplier=float(st.session_state["opt_cap_mult"]),
                    supply_slack_factor=float(st.session_state["opt_sup_factor"])
                )
                st.session_state["last_opt_sol"] = sol

        # Process and display solution
        sol = st.session_state.get("last_opt_sol", None)

        # Defensive upgrade for stale session state from prior versions
        if sol is not None and sol.get("status") == "optimal" and ("demand_df" not in sol or "supply_df" not in sol):
            model = MultimodalFreightModel()
            sol = model.build_and_solve(
                flows_df,
                capacity_multiplier=float(st.session_state.get("opt_cap_mult", 1.25)),
                supply_slack_factor=float(st.session_state.get("opt_sup_factor", 1.25))
            )
            st.session_state["last_opt_sol"] = sol

        if sol is not None:
            st.markdown("---")

            # 4. Infeasible / Unbounded Diagnosis
            if sol["status"] != "optimal":
                st.error(
                    f"⚠️ **Optimization Problem Infeasible or Unbounded (Solver Code: {sol.get('solver_status', 'N/A')})**"
                )
                rep_msg = sol.get('message', 'No feasible solution found.')
                cap_m = sol.get('capacity_multiplier', 1.0)
                sup_f = sol.get('supply_slack_factor', 1.0)

                st.markdown(
                    f"""
                    <div style="background-color: #FEF2F2; border: 1px solid #FCA5A5; border-left: 4px solid #DC2626; padding: 14px 18px; border-radius: 6px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: #991B1B; font-size: 14px; margin-bottom: 6px;">
                            Mathematical Infeasibility Diagnosis:
                        </div>
                        <div style="font-size: 13px; color: #7F1D1D; line-height: 1.55;">
                            The SciPy HiGHS solver detected that no non-negative flow vector <b>x ≥ 0</b> can simultaneously satisfy all linear constraints:<br>
                            • <b>Reported Solver Message:</b> {rep_msg}<br>
                            • <b>Active Capacity Headroom:</b> {cap_m:.2f}x | <b>Active Supply Headroom:</b> {sup_f:.2f}x
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    "**Theoretical Explanation:**\n\n"
                    "When the Corridor Capacity Headroom Multiplier or Origin Supply Headroom Factor is set below 1.00x, "
                    "the total throughput capacity on one or more critical corridors is strictly less than the required destination demand:"
                )
                st.latex(r"\sum_{m \in \mathcal{M}} u_{i,j,m} < d_{i,j,k} \quad \text{or} \quad S_{i,k} < \sum_{j \in \mathcal{D}} d_{i,j,k}")
                st.markdown(
                    "Under strict demand conservation, demand shortfall is not permitted, "
                    "causing the primal linear program to have an empty feasible region.\n\n"
                    "**Remediation:** Click **'↺ Reset to Baseline (1.00x)'** above or increase the headroom multipliers to at least 1.00x to restore primal feasibility."
                )
                return

            # 5. Optimal Solution Metrics Display
            st.success(
                f"✅ **Optimal Solution Found!** Solved by **{sol.get('solver_name', 'SciPy HiGHS')}** "
                f"(Status Code 0: Optimal) in **{sol['solver_runtime']:.3f} seconds**."
            )

            # Convert to display formats
            obj_val_k = sol["objective_value"]
            base_val_k = sol["observed_baseline_cost"]
            savings_k = sol["cost_savings"]
            savings_pct = sol["savings_percent"]

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric(
                    "Optimized Logistics Cost",
                    f"${obj_val_k / 1e3:,.2f} M",
                    delta=f"${obj_val_k:,.0f}k USD",
                    help="Total national freight transportation cost under optimal modal allocation."
                )
            with m2:
                st.metric(
                    "Observed Baseline Cost",
                    f"${base_val_k / 1e3:,.2f} M",
                    delta="Historical 2022",
                    help="Calculated shipping cost using actual observed 2022 transportation mode choices."
                )
            with m3:
                st.metric(
                    "Modeled Cost Reduction",
                    f"${savings_k / 1e3:,.2f} M",
                    delta=f"-{savings_pct:.2f}% Savings",
                    help="National expenditure reduction achieved by reallocating flows to lower-cost rail/water routes."
                )
            with m4:
                st.metric(
                    "Active Bottlenecks",
                    f"{sol.get('num_binding_corridors', 0)} Corridors",
                    delta=f"{sol.get('num_decision_vars', 0):,} Variables",
                    help="Corridor-mode capacity bounds that are 100% utilized and have positive dual shadow prices."
                )

            st.markdown(
                f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0D9488; padding: 12px 16px; border-radius: 6px; margin: 12px 0 16px 0;">
                    <span style="font-weight: 700; color: #0F172A; font-size: 13.5px;">
                        Operations Research Optimization Insight:
                    </span><br>
                    <span style="font-size: 12.5px; color: #475569; line-height: 1.5;">
                        The HiGHS linear program achieves a <b>${savings_k / 1e3:,.2f} Million ({savings_pct:.2f}%) cost reduction</b> 
                        relative to the observed 2022 baseline. It accomplishes this by shifting long-haul heavy bulk commodities 
                        (e.g. agricultural grains, crushed stone, non-metallic minerals) from high-rate highway trucking ($0.18/ton-mile) 
                        onto Class I rail ($0.045/ton-mile) and inland waterways ($0.030/ton-mile) up to the exact threshold where corridor capacity constraints become binding.
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 6. Detailed Analytical Results Tabs
            tab_alloc, tab_demand, tab_supply, tab_cap, tab_binding = st.tabs([
                "📦 Freight Allocation Ledger",
                "🎯 Demand Satisfaction",
                "🏭 Origin Supply Utilization",
                "🛣️ Corridor Capacity Utilization",
                "⚡ Binding Constraints & Shadow Prices"
            ])

            # Tab 1: Freight Allocation Ledger
            with tab_alloc:
                st.subheader("Multimodal Freight Flow Allocation Ledger")
                st.caption(
                    "Optimal decision variable values x*_{i,j,k,m} detailing flow volume, mode allocation, and route expenditure."
                )

                alloc_df = sol["allocations_df"].copy()

                # Filter options
                filter_c1, filter_c2 = st.columns([2, 1])
                with filter_c1:
                    search_alloc = st.text_input("Filter Allocation by Region Name:", "", key="search_alloc_text")
                with filter_c2:
                    mode_filter_opt = st.selectbox(
                        "Filter Transport Mode:",
                        ["All Modes"] + [FAF6_MODES[m] for m in sorted(list(alloc_df["mode"].unique()))],
                        key="alloc_mode_filter"
                    )

                display_alloc = alloc_df[alloc_df["allocated_tons"] > 0].copy()
                if search_alloc:
                    display_alloc = display_alloc[
                        display_alloc["orig_name"].str.contains(search_alloc, case=False, na=False) |
                        display_alloc["dest_name"].str.contains(search_alloc, case=False, na=False)
                    ]
                if mode_filter_opt != "All Modes":
                    display_alloc = display_alloc[display_alloc["mode_name"] == mode_filter_opt]

                formatted_alloc = pd.DataFrame({
                    "Origin Region": display_alloc["orig_name"],
                    "Destination Region": display_alloc["dest_name"],
                    "Commodity": display_alloc["commodity_name"],
                    "SCTG": display_alloc["comm"].apply(lambda c: f"{c:02d}"),
                    "Transport Mode": display_alloc["mode_name"],
                    "Distance (mi)": display_alloc["distance"].apply(lambda d: f"{d:,.0f}"),
                    "Unit Cost ($/ton)": display_alloc["unit_cost"].apply(lambda c: f"${c:.2f}"),
                    "Allocated Volume (k tons)": display_alloc["allocated_tons"].apply(lambda v: f"{v:,.1f}"),
                    "Route Cost ($k)": display_alloc["allocated_cost"].apply(lambda v: f"${v:,.1f}")
                })

                st.dataframe(formatted_alloc, use_container_width=True, hide_index=True, height=360)

            # Tab 2: Demand Satisfaction
            with tab_demand:
                st.subheader("Destination Regional Demand Satisfaction")
                st.caption(
                    "Verifies strict fulfillment of Demand Conservation equality constraints (sum_m x = d) for each commodity."
                )

                demand_df = sol.get("demand_df", pd.DataFrame())
                if not demand_df.empty:
                    d_c1, d_c2, d_c3 = st.columns(3)
                    with d_c1:
                        st.metric("Total Required Demand", f"{sol.get('total_demand_tons', 0):,.1f} k tons")
                    with d_c2:
                        st.metric("Total Delivered Freight", f"{sol.get('total_freight_tons', 0):,.1f} k tons")
                    with d_c3:
                        st.metric("Demand Satisfaction Rate", "100.0%", delta="Zero Shortfall")

                    marg_deliv_col = "marginal_delivery_cost" if "marginal_delivery_cost" in demand_df.columns else ("marginal_demand_cost" if "marginal_demand_cost" in demand_df.columns else None)
                    formatted_demand = pd.DataFrame({
                        "Origin Region": demand_df["orig_name"],
                        "Destination Region": demand_df["dest_name"],
                        "Commodity": demand_df["commodity_name"] if "commodity_name" in demand_df.columns else demand_df.get("comm", ""),
                        "Required Demand (k tons)": demand_df["required_demand_tons"].apply(lambda v: f"{v:,.1f}"),
                        "Delivered Flow (k tons)": demand_df["delivered_flow_tons"].apply(lambda v: f"{v:,.1f}"),
                        "Satisfaction (%)": demand_df["satisfaction_pct"].apply(lambda v: f"{v:.1f}%"),
                        "Marginal Delivery Cost ($/ton)": demand_df[marg_deliv_col].apply(lambda v: f"${v:.4f}") if marg_deliv_col else ["$0.0000"] * len(demand_df)
                    })
                    st.dataframe(formatted_demand, use_container_width=True, hide_index=True, height=340)

            # Tab 3: Supply Utilization
            with tab_supply:
                st.subheader("Origin Regional Supply Limits & Inventory Utilization")
                st.caption(
                    "Analysis of Origin Regional Supply constraints (sum_{j,m} x <= S_{i,k}) across production gateways."
                )

                supply_df = sol.get("supply_df", pd.DataFrame())
                if not supply_df.empty:
                    avg_sup_util = supply_df["utilization_pct"].mean()
                    binding_sup_count = sol.get("num_binding_supplies", 0)

                    s_c1, s_c2, s_c3 = st.columns(3)
                    with s_c1:
                        st.metric("Average Regional Supply Utilization", f"{avg_sup_util:.1f}%")
                    with s_c2:
                        st.metric("Binding Supply Bottlenecks", f"{binding_sup_count} Facilities")
                    with s_c3:
                        st.metric("Supply Headroom Setting", f"{sol.get('supply_slack_factor', 1.0):.2f}x")

                    formatted_supply = pd.DataFrame({
                        "Origin Region": supply_df["orig_name"],
                        "Commodity": supply_df["commodity_name"],
                        "Supply Limit (k tons)": supply_df["supply_limit_tons"].apply(lambda v: f"{v:,.1f}"),
                        "Dispatched Volume (k tons)": supply_df["dispatched_tons"].apply(lambda v: f"{v:,.1f}"),
                        "Slack Unused (k tons)": supply_df["slack_tons"].apply(lambda v: f"{v:,.1f}"),
                        "Utilization (%)": supply_df["utilization_pct"].apply(lambda v: f"{v:.1f}%"),
                        "Status": supply_df["is_binding"].apply(lambda b: "🔴 Binding (Bottleneck)" if b else "🟢 Slack Available"),
                        "Dual Shadow Price ($/ton)": supply_df["shadow_price"].apply(lambda v: f"${v:.4f}")
                    })
                    st.dataframe(formatted_supply, use_container_width=True, hide_index=True, height=340)

            # Tab 4: Corridor Capacity Utilization
            with tab_cap:
                st.subheader("Corridor-Mode Capacity Utilization Ledger")
                st.caption(
                    "Examines physical throughput on each corridor mode conduit relative to maximum capacity bounds u_{i,j,m}."
                )

                cap_df = sol.get("capacity_df", pd.DataFrame())
                if not cap_df.empty:
                    avg_cap_util = cap_df["utilization_pct"].mean()
                    max_shadow = cap_df["shadow_price"].max()

                    u_c1, u_c2, u_c3 = st.columns(3)
                    with u_c1:
                        st.metric("Average Corridor Utilization", f"{avg_cap_util:.1f}%")
                    with u_c2:
                        st.metric("Binding Corridor Bottlenecks", f"{sol.get('num_binding_corridors', 0)} Conduits")
                    with u_c3:
                        st.metric("Peak Dual Shadow Price", f"${max_shadow:.2f} / ton")

                    formatted_cap = pd.DataFrame({
                        "Origin Region": cap_df["orig_name"],
                        "Destination Region": cap_df["dest_name"],
                        "Transport Mode": cap_df["mode_name"],
                        "Capacity Limit (k tons)": cap_df["capacity"].apply(lambda v: f"{v:,.1f}"),
                        "Allocated Volume (k tons)": cap_df["allocated"].apply(lambda v: f"{v:,.1f}"),
                        "Slack Headroom (k tons)": cap_df["slack_tons"].apply(lambda v: f"{v:,.1f}"),
                        "Utilization (%)": cap_df["utilization_pct"].apply(lambda v: f"{v:.1f}%"),
                        "Status": cap_df["is_binding"].apply(lambda b: "🔴 Binding (Bottleneck)" if b else "🟢 Flow Under Cap"),
                        "Dual Shadow Price ($/ton)": cap_df["shadow_price"].apply(lambda v: f"${v:.4f}")
                    })
                    st.dataframe(formatted_cap, use_container_width=True, hide_index=True, height=340)

            # Tab 5: Binding Constraints & Shadow Prices
            with tab_binding:
                st.subheader("Binding Constraints & Dual Shadow Price Valuation")
                st.caption(
                    "Identifies active network bottlenecks (slack = 0, utilization >= 99.9%) and reports their exact shadow prices."
                )

                st.markdown("""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0D9488; padding: 12px 16px; border-radius: 6px; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 13.5px; margin-bottom: 4px;">
                        Interpretation of Dual Shadow Prices (π):
                    </div>
                    <div style="font-size: 12.5px; color: #475569; line-height: 1.5;">
                        The <b>dual shadow price</b> represents the marginal rate of reduction in the optimal total system cost 
                        per unit expansion of a binding physical constraint.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.latex(r"\pi_{i,j,m} = -\frac{\partial Z^*}{\partial u_{i,j,m}} \ge 0")

                st.caption(
                    "For every additional short ton of throughput capacity added to a binding corridor, total national freight transportation cost decreases by exactly π dollars. "
                    "Corridors with zero shadow price have positive slack headroom; expanding them produces zero cost reduction."
                )

                binding_corrs = sol.get("binding_corridors_df", pd.DataFrame())

                if not binding_corrs.empty:
                    st.markdown(f"**Identified {len(binding_corrs)} Binding Corridor Bottlenecks (Ranked by Dual Shadow Price):**")
                    formatted_binding = pd.DataFrame({
                        "Origin Region": binding_corrs["orig_name"],
                        "Destination Region": binding_corrs["dest_name"],
                        "Transport Mode": binding_corrs["mode_name"],
                        "Throughput Bound (k tons)": binding_corrs["capacity"].apply(lambda v: f"{v:,.1f}"),
                        "Allocated Flow (k tons)": binding_corrs["allocated"].apply(lambda v: f"{v:,.1f}"),
                        "Utilization (%)": binding_corrs["utilization_pct"].apply(lambda v: f"{v:.1f}%"),
                        "Dual Shadow Price ($/ton)": binding_corrs["shadow_price"].apply(lambda v: f"${v:.4f}"),
                        "Economic Priority": binding_corrs["shadow_price"].apply(
                            lambda p: "High Priority (High Savings)" if p > 2.0 else ("Medium Priority" if p > 0.5 else "Low Priority")
                        )
                    })
                    st.dataframe(formatted_binding, use_container_width=True, hide_index=True, height=320)
                else:
                    st.info("No corridor capacity constraints are currently binding. All flows operate with positive slack headroom.")

            # Save Model to SQLite
            st.markdown("---")
            st.subheader("Model Persistence & Scenario Storage")
            save_col1, save_col2 = st.columns([3, 1])
            with save_col1:
                model_save_name = st.text_input(
                    "Save This Model Configuration As:",
                    value=f"Multimodal_LP_Cap{sol.get('capacity_multiplier', 1.0):.2f}_Sup{sol.get('supply_slack_factor', 1.0):.2f}"
                )
            with save_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Save Model to Database"):
                    db.save_model(
                        name=model_save_name,
                        model_type="Multimodal_LP",
                        params={"capacity_multiplier": sol.get("capacity_multiplier"), "supply_slack_factor": sol.get("supply_slack_factor")},
                        results={"objective_value": sol["objective_value"], "savings_percent": sol["savings_percent"]},
                        obj_val=sol["objective_value"]
                    )
                    st.success(f"Model '{model_save_name}' saved to SQLite database!")
