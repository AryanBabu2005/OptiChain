"""
Freight Disruption Scenarios & Resilience Analysis UI for OptiChain.
Models real-world logistical shocks (Baltimore bridge, Mississippi drought, rail stoppage)
using linear programming with unmet demand slack variables and mode substitution.
"""

from typing import List, Tuple
import streamlit as st
import pandas as pd
from src.models.disruption_model import FreightDisruptionSimulator
from src.network.geography import FAF6_MODES, FAF6_DOMESTIC_ZONES
from src.visualization.charts import plot_disruption_comparison
from src.database.storage import OptiChainDatabase

# Grounded Real-World Case Studies
REAL_WORLD_PRESETS = {
    "Case Study 1: Baltimore Key Bridge & Port Closure (March 2024)": {
        "summary": "On March 26, 2024, the container ship Dali struck the Francis Scott Key Bridge, temporarily blocking the shipping channel into the Port of Baltimore (Zone 241).",
        "details": "Baltimore is a primary East Coast hub for automobile roll-on/roll-off cargo (SCTG 36) and export coal (SCTG 15). Cargo had to be redirected by road and rail to ports in Philadelphia (421) and Norfolk/Hampton Roads (512).",
        "corridors": [(241, 421), (241, 363), (241, 131)],
        "modes": [1, 3],
        "retention": 0.15,
        "cost_surge": 1.30,
        "demand_surge": 1.05
    },
    "Case Study 2: Mississippi River Barge Low-Water Drought (Fall 2022)": {
        "summary": "Severe drought throughout the central US dropped Mississippi River depths to historic lows, restricting barge tow sizes and drafts during peak harvest season.",
        "details": "Barges on the Mississippi (Mode 3) normally carry over 60% of US grain exports down to Gulf Coast terminals in Louisiana. The capacity restriction forced agricultural shippers in Iowa, Illinois, and Missouri to divert grain onto Class I railroads and long-distance trucks at substantially higher cost.",
        "corridors": [(172, 223), (292, 223), (471, 221)],
        "modes": [3],
        "retention": 0.25,
        "cost_surge": 1.40,
        "demand_surge": 1.0
    },
    "Case Study 3: Nationwide Freight Rail Labor Stoppage": {
        "summary": "A hypothetical nationwide shutdown of Class I railroads (Mode 2) due to labor disputes or infrastructure failure.",
        "details": "Freight rail moves over 28% of all ton-miles in the US, particularly heavy bulk commodities (coal, grains, chemicals, and intermodal containers). This scenario shows what happens if rail capacity drops to zero and the road network must try to absorb the volume.",
        "corridors": [],
        "modes": [2],
        "retention": 0.0,
        "cost_surge": 1.50,
        "demand_surge": 1.0
    },
    "Case Study 4: Diesel Fuel Price Surge (+40% Spike)": {
        "summary": "A sharp rise in global petroleum prices increasing motor carrier operating costs by 40%.",
        "details": "Because trucks consume significantly more fuel per ton-mile than rail or barges, a fuel spike changes the economic breakeven distance, making rail and intermodal options more competitive on shorter corridors.",
        "corridors": [],
        "modes": [],
        "retention": 1.0,
        "cost_surge": 1.40,
        "demand_surge": 1.0
    },
    "Custom Scenario: Build Your Own What-If": {
        "summary": "Select specific origin-destination pairs or transport modes to simulate a custom regional shock.",
        "details": "Use the sliders and selection boxes below to define your own scenario.",
        "corridors": [],
        "modes": [],
        "retention": 0.50,
        "cost_surge": 1.15,
        "demand_surge": 1.0
    }
}

def render_disruption_ui(flows_df: pd.DataFrame, view_mode: str = "simulator"):
    db = OptiChainDatabase()

    if view_mode == "comparison":
        st.header("Resilience Stress-Testing & Scenario History")
        st.markdown("""
        This page allows you to compare how different disruption scenarios impact the network, 
        and review scenarios saved in the local SQLite database.
        """)

        saved_scenarios = db.list_scenarios()
        if not saved_scenarios:
            st.info("No saved scenarios in the database yet. You can run any scenario in the simulator and click 'Save to Database' to compare them here.")
        else:
            st.subheader(f"Saved Scenarios ({len(saved_scenarios)} Total)")
            st.dataframe(pd.DataFrame(saved_scenarios), use_container_width=True)

        st.markdown("---")
        st.subheader("Uniform Capacity Reduction Matrix (Stress-Testing)")
        st.markdown("""
        To understand systemic resilience, we can systematically test what happens when network-wide corridor 
        capacity is throttled down from 90% to 10% of normal capacity.
        """)

        if st.button("Run Systemic Stress-Test", type="primary"):
            with st.spinner("Running optimization across 5 capacity levels..."):
                sim = FreightDisruptionSimulator()
                levels = [0.90, 0.75, 0.50, 0.25, 0.10]
                stress_rows = []
                for ret in levels:
                    res_lvl = sim.simulate_disruption(flows_df, capacity_retention=ret)
                    stress_rows.append({
                        "Remaining Capacity": f"{int(ret*100)}%",
                        "Capacity Lost": f"-{int((1-ret)*100)}%",
                        "Resilience Service Ratio": f"{res_lvl['resilience_service_ratio']:.1f}%",
                        "Unmet Freight (k tons)": f"{res_lvl['unmet_demand_tons']:,.1f}",
                        "Cost Change": f"${res_lvl['cost_increase']:,.2f}",
                        "Percentage Cost Surge": f"+{res_lvl['cost_increase_percent']:.1f}%"
                    })
                st.table(pd.DataFrame(stress_rows))

    else:
        st.header("Network Disruption & Resilience Simulator")
        st.markdown(r"""
        How resilient is the freight network when critical infrastructure fails?
        
        In this module, we model corridor closures and mode shutdowns. When a route is restricted, 
        the linear program attempts to **reroute freight onto alternative modes or paths**. If no alternative 
        capacity exists, freight becomes **unmet demand** with an economic shortage penalty ($P = \$1,000/\text{ton}$).
        """)

        # 1. Preset Selection
        st.subheader("1. Select Real-World Disruption Incident")
        preset_choice = st.selectbox("Scenario Preset", list(REAL_WORLD_PRESETS.keys()))
        preset_data = REAL_WORLD_PRESETS[preset_choice]

        st.markdown(f"""
        <div class="opti-card" style="border-left: 4px solid #DC2626; background: #FFFBFB; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-weight: 700; color: #991B1B; font-size: 14px;">INCIDENT DOSSIER: {preset_choice}</span>
                <span class="opti-pill opti-pill-amber" style="font-size: 10px;">HISTORICAL CASE</span>
            </div>
            <div style="font-size: 13px; color: #475569; line-height: 1.5;">
                <b>Logistics Impact:</b> {preset_data['summary']}<br>
                <b>Empirical Background:</b> {preset_data['details']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Parameters
        with st.expander("2. Scenario Parameters (Adjustable)", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                # Top corridors
                top_corrs = flows_df.groupby(["dms_orig", "dms_dest", "orig_name", "dest_name"])["tons_2022"].sum().sort_values(ascending=False).head(20).reset_index()
                corr_options = [(int(r["dms_orig"]), int(r["dms_dest"])) for _, r in top_corrs.iterrows()]
                default_corrs = [c for c in preset_data["corridors"] if c in corr_options]

                selected_corrs = st.multiselect(
                    "Sever Specific Corridors (Total or Partial Closure)",
                    options=corr_options,
                    default=default_corrs,
                    format_func=lambda c: f"{FAF6_DOMESTIC_ZONES.get(c[0], {}).get('name', '')} -> {FAF6_DOMESTIC_ZONES.get(c[1], {}).get('name', '')}"
                )

                disrupted_modes = st.multiselect(
                    "Disrupt Entire Transportation Modes",
                    options=[1, 2, 3, 4, 5],
                    default=preset_data["modes"],
                    format_func=lambda m: f"Mode {m}: {FAF6_MODES.get(m, '')}"
                )

            with c2:
                retention = st.slider(
                    "Remaining Capacity on Disrupted Routes (α)", 0.0, 1.0, float(preset_data["retention"]), 0.05,
                    help="1.0 = normal capacity, 0.0 = total route closure"
                )
                cost_surge = st.slider(
                    "Cost Surcharge Multiplier (Detours/Fuel)", 1.0, 2.5, float(preset_data["cost_surge"]), 0.05,
                    help="Represents higher fuel prices, detour circuity, or surge spot rates"
                )
                demand_surge = st.slider(
                    "Demand Change Factor", 0.8, 1.5, float(preset_data["demand_surge"]), 0.05,
                    help="1.0 = normal demand, 1.2 = 20% surge in demand"
                )
                penalty = st.number_input("Shortage Penalty for Unmet Demand ($/ton)", value=1000.0, step=100.0,
                                          help="Penalty cost per ton of freight that cannot be moved")

        if st.button("Run Disruption Simulation", type="primary"):
            with st.spinner("Re-optimizing network flows with HiGHS..."):
                sim = FreightDisruptionSimulator(unmet_demand_penalty=penalty)
                res = sim.simulate_disruption(
                    flows_df,
                    disrupted_corridors=selected_corrs,
                    disrupted_modes=disrupted_modes,
                    capacity_retention=retention,
                    cost_surge_factor=cost_surge,
                    demand_surge_factor=demand_surge
                )

            if res["status"] == "optimal":
                st.session_state["last_disruption_res"] = res
                st.success("Simulation complete! The network response has been solved.")

                # KPI Cards
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    svc_val = res['resilience_service_ratio']
                    st.metric(
                        "Resilience Service Ratio",
                        f"{svc_val:.1f}%",
                        delta=f"{svc_val - 100.0:.1f}%" if svc_val < 100.0 else "100% Demand Met",
                        help="Tonnage successfully served divided by total demand"
                    )
                with k2:
                    st.metric(
                        "Unmet Freight Demand",
                        f"{res['unmet_demand_tons']:,.1f}k tons",
                        help="Tonnage stranded due to lack of alternative capacity"
                    )
                with k3:
                    st.metric(
                        "Logistics Cost Increase",
                        f"${res['cost_increase']:,.2f}",
                        delta=f"+{res['cost_increase_percent']:.1f}% vs Baseline",
                        help="Additional operational cost from detours and mode shifting"
                    )
                with k4:
                    st.metric(
                        "Total Cost (Incl. Penalties)",
                        f"${res['total_objective_cost']:,.2f}",
                        help="Modeled transport cost plus economic shortage penalties"
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                st.plotly_chart(
                    plot_disruption_comparison(
                        res["baseline_cost"] / 1e6, res["total_objective_cost"] / 1e6,
                        res["total_system_demand"], res["freight_served_tons"]
                    ),
                    use_container_width=True
                )

                # Mode substitution breakdown
                st.subheader("Mode Substitution Analysis")
                st.caption("How freight shifted between modes in response to the disruption:")
                st.dataframe(pd.DataFrame(res["mode_shifts"]), use_container_width=True)

                # Save Scenario form
                st.markdown("---")
                save_c1, save_c2 = st.columns([3, 1])
                with save_c1:
                    scen_name = st.text_input("Save This Scenario to SQLite As:", value=f"Run_{preset_choice[:20].strip()}")
                with save_c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Save Scenario"):
                        db.save_scenario(
                            name=scen_name,
                            description=f"Preset: {preset_choice} | Retention: {retention} | Surge: {cost_surge}",
                            config={"preset": preset_choice, "retention": retention, "cost_surge": cost_surge, "penalty": penalty},
                            results=res,
                            service_ratio=res["resilience_service_ratio"],
                            total_cost=res["total_objective_cost"]
                        )
                        st.success(f"Scenario '{scen_name}' saved to database!")
            else:
                st.error(f"Solver Error: {res.get('message', 'Infeasible')}")
