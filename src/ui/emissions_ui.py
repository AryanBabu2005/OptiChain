"""
Emissions & Green Freight Analysis UI for OptiChain.
Grounded environmental economics using EPA SmartWay factors to evaluate
modal carbon emissions and the cost-vs-carbon Pareto frontier.
"""

import streamlit as st
import pandas as pd
from src.models.emissions_model import GreenLogisticsEngine, EMISSION_FACTORS_G_PER_TON_MILE
from src.visualization.charts import plot_pareto_frontier, plot_emissions_breakdown

def render_emissions_ui(flows_df: pd.DataFrame):
    st.header("Green Logistics & Scope 3 Freight Decarbonization")
    st.markdown(r"""
    <div class="opti-card" style="border-left: 4px solid #059669; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 700; color: #065F46; font-size: 14px;">Scope 3 Carbon Accounting Standard</span>
            <span class="opti-pill opti-pill-teal" style="font-size: 10px;">EPA SmartWay & GLEC</span>
        </div>
        <div style="font-size: 13px; color: #475569; line-height: 1.55;">
            Evaluates greenhouse gas emissions across national freight flows using official <b>EPA SmartWay</b> 
            and <b>Global Logistics Emissions Council (GLEC)</b> emission factors per ton-mile. 
            Solves a bi-objective linear program generating the <b>Pareto Optimal Frontier</b> between logistics cost and carbon emissions.
        </div>
    </div>
    """, unsafe_allow_html=True)

    engine = GreenLogisticsEngine()

    with st.spinner("Calculating freight emissions across the network..."):
        emiss_summary = engine.evaluate_network_emissions(flows_df)

    # Clean KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Network Carbon",
            value=f"{emiss_summary['total_co2e_metric_tons']:,.0f} t CO2e",
            help="Total carbon footprint calculated from ton-miles and mode emissions factors"
        )
    with col2:
        st.metric(
            label="Carbon (Megatons)",
            value=f"{emiss_summary['total_co2e_megatons']:.3f} Mt",
            help="1 Megaton = 1,000,000 Metric Tons of CO2e"
        )
    with col3:
        st.metric(
            label="Average Carbon Intensity",
            value=f"{emiss_summary['average_network_intensity_g_per_tm']} g/ton-mile",
            help="Fleet-weighted grams of CO2e emitted per ton-mile across active corridors"
        )
    with col4:
        st.metric(
            label="Rail vs Truck Cleanliness",
            value="7.3x Lower",
            delta="-86.4% CO2/ton-mile",
            help="Class I Freight Rail emits ~22.0 g/ton-mile vs Trucking ~161.8 g/ton-mile"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🌱 Cost vs. Carbon Pareto Frontier", "📊 Emissions by Transport Mode", "📜 EPA & GLEC Benchmark Factors"])

    with tab1:
        st.subheader("Bi-Objective Optimization: Finding the Trade-off Between Cost and Carbon")
        st.markdown("""
        When companies want to reduce their supply chain carbon footprint, they face a practical question: 
        *How much extra will it cost to shift freight from fast highway trucks to slower, lower-emission freight rail or waterways?*
        
        Using **weighted-sum scalarization**, we solve a series of linear programs where the objective balances normalized cost and normalized emissions:
        $$\\min Z = (1 - \\alpha) \\cdot \\text{Cost} + \\alpha \\cdot \\text{Emissions}$$
        - When $\\alpha = 0$, the solver only cares about minimizing financial cost.
        - When $\\alpha = 1$, the solver only cares about minimizing carbon emissions.
        - The resulting curve is the **Pareto Efficient Frontier**.
        """)

        num_frontier_pts = st.slider("Number of Trade-Off Steps to Evaluate", min_value=5, max_value=11, value=7, step=2)

        if st.button("Calculate Pareto Frontier", type="primary"):
            with st.spinner("Solving multi-objective LP sequence..."):
                frontier_pts = engine.generate_pareto_frontier(flows_df, num_points=num_frontier_pts)

            if frontier_pts:
                st.session_state["pareto_points"] = frontier_pts
                st.success("Frontier calculated successfully!")

        if "pareto_points" in st.session_state:
            pts = st.session_state["pareto_points"]
            st.plotly_chart(plot_pareto_frontier(pts), use_container_width=True)

            st.subheader("Pareto Trade-Off Policy Table")
            df_pts = pd.DataFrame(pts)
            st.dataframe(df_pts, use_container_width=True)

            # Marginal Abatement Cost (MAC)
            first_pt = df_pts.iloc[0]
            last_pt = df_pts.iloc[-1]
            cost_increase = last_pt["total_logistics_cost"] - first_pt["total_logistics_cost"]
            carbon_reduced = first_pt["total_co2e_metric_tons"] - last_pt["total_co2e_metric_tons"]
            mac = (cost_increase / carbon_reduced) if carbon_reduced > 0 else 0.0

            st.info(f"""
            **Economic Interpretation (Marginal Abatement Cost):**  
            Moving from the least-cost policy to the greenest policy eliminates **{carbon_reduced:,.1f} metric tons of CO2e** 
            at an additional logistics expense of **${cost_increase:,.2f}**.  
            This represents an average cost of **${mac:,.2f} per ton of CO2 removed**, which is a practical benchmark for comparing against internal carbon pricing or voluntary carbon credits.
            """)

    with tab2:
        st.subheader("Carbon Emissions Breakdown by Transportation Mode")
        st.plotly_chart(plot_emissions_breakdown(emiss_summary["mode_breakdown_df"]), use_container_width=True)

        st.subheader("Modal Emissions and Share Data")
        st.dataframe(emiss_summary["mode_breakdown_df"], use_container_width=True)

    with tab3:
        st.subheader("Official GLEC and EPA SmartWay Emission Factors")
        st.markdown("""
        The emissions coefficients used in this model are sourced from the **Global Logistics Emissions Council (GLEC) Framework Version 3.0** 
        and the **US EPA SmartWay Transport Partnership**:
        """)
        glec_data = [
            {"Transport Mode": "1: Highway Truck (Class 8 Diesel)", "Emissions Factor": "161.8 g CO2e / ton-mile", "Context": "Standard tractor-trailer long-haul average", "Relative Carbon": "Baseline"},
            {"Transport Mode": "2: Class I Freight Rail", "Emissions Factor": "22.0 g CO2e / ton-mile", "Context": "Diesel-electric locomotives; high fuel efficiency", "Relative Carbon": "-86.4% vs Truck"},
            {"Transport Mode": "3: Inland Waterway & Barge", "Emissions Factor": "19.3 g CO2e / ton-mile", "Context": "High-capacity river tows (Mississippi / Ohio rivers)", "Relative Carbon": "-88.1% vs Truck"},
            {"Transport Mode": "4: Air Cargo", "Emissions Factor": "1,520.0 g CO2e / ton-mile", "Context": "Dedicated freighter aircraft for high-value urgent goods", "Relative Carbon": "9.4x higher than Truck"},
            {"Transport Mode": "5: Intermodal Rail-Truck", "Emissions Factor": "65.0 g CO2e / ton-mile", "Context": "Weighted blend of rail line-haul and local truck drayage", "Relative Carbon": "-59.8% vs Truck"},
            {"Transport Mode": "6: Pipeline (Liquid/Gas)", "Emissions Factor": "15.0 g CO2e / ton-mile", "Context": "Continuous pumping infrastructure", "Relative Carbon": "Lowest physical footprint"}
        ]
        st.table(pd.DataFrame(glec_data))
