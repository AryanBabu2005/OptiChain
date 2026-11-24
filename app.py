"""
OptiChain: Multimodal Freight Network Optimization, Capacity Planning & Disruption Resilience.
Official Research Platform using the Freight Analysis Framework (FAF6 2022 Benchmark).
B.Tech Project in Mathematical Innovation & Operations Research.
"""

from typing import Optional
import os
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# Page Configuration
st.set_page_config(
    page_title="OptiChain — FAF6 Freight Optimization Platform",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Comprehensive Humanized Design System & Typography
st.markdown("""
<style>
    /* Google Fonts: Plus Jakarta Sans for UI/Prose, JetBrains Mono for Numbers/Math */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        --color-navy: #0F172A;
        --color-slate-dark: #1E293B;
        --color-slate-muted: #64748B;
        --color-teal: #0D9488;
        --color-teal-hover: #0F766E;
        --color-blue: #2563EB;
        --color-bg-canvas: #F8FAFC;
        --color-surface-white: #FFFFFF;
        --color-border: #E2E8F0;
        --color-border-subtle: #F1F5F9;
    }

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: var(--font-sans);
        color: var(--color-navy);
        background-color: var(--color-bg-canvas);
    }

    /* Hide generic Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}

    /* Main Container Padding */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
    section[data-testid="stSidebar"] * {
        color: #F8FAFC;
        font-family: var(--font-sans);
    }

    /* Hero Banner Component */
    .opti-hero-banner {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }
    .opti-hero-title {
        font-size: 24px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin: 0 0 4px 0;
    }
    .opti-hero-subtitle {
        font-size: 13.5px;
        color: #64748B;
        line-height: 1.5;
        margin: 0;
    }

    /* Pill Badges */
    .opti-pill {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .opti-pill-navy {
        background-color: #0F172A;
        color: #FFFFFF;
    }
    .opti-pill-teal {
        background-color: #CCFBF1;
        color: #0F766E;
        border: 1px solid #99F6E4;
    }
    .opti-pill-blue {
        background-color: #DBEAFE;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    .opti-pill-amber {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .opti-pill-slate {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #E2E8F0;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.07);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 11.5px;
        font-weight: 600;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] {
        font-size: 23px;
        font-weight: 700;
        color: #0F172A !important;
        font-family: var(--font-mono);
        letter-spacing: -0.02em;
    }

    /* Custom Cards */
    .opti-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .opti-card-title {
        font-size: 15px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 6px;
    }
    .opti-card-body {
        font-size: 13px;
        color: #475569;
        line-height: 1.55;
    }

    /* Primary and Secondary Buttons */
    button[kind="primary"] {
        background-color: #0D9488 !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 7px !important;
        padding: 8px 18px !important;
        font-size: 13.5px !important;
        box-shadow: 0 1px 2px rgba(13, 148, 136, 0.2) !important;
        transition: all 0.15s ease !important;
    }
    button[kind="primary"]:hover {
        background-color: #0F766E !important;
        box-shadow: 0 2px 4px rgba(13, 148, 136, 0.3) !important;
    }
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
        font-weight: 600 !important;
        border-radius: 7px !important;
        font-size: 13.5px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        padding: 8px 16px !important;
    }
    button[aria-selected="true"] {
        color: #0D9488 !important;
        border-bottom-color: #0D9488 !important;
    }

    /* Dataframe table styling */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
    }

    /* Segmented Control Sub-Navigation Styling */
    div[data-testid="stSegmentedControl"] {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 6px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        margin-bottom: 22px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: 8px !important;
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        padding: 9px 18px !important;
        min-height: 40px !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        border: 1px solid transparent !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
        background-color: #0D9488 !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 4px rgba(13, 148, 136, 0.3) !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="false"] {
        color: #334155 !important;
        background-color: #F8FAFC !important;
        border-color: #E2E8F0 !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="false"]:hover {
        background-color: #EEF2F6 !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }

    /* Subheader divider */
    hr {
        border-color: #E2E8F0;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Import UI Modules
from src.ui.dashboard import render_executive_dashboard
from src.ui.dataset_explorer import render_dataset_explorer
from src.ui.freight_network import render_freight_network
from src.ui.optimizer import render_optimizer_ui
from src.ui.disruption import render_disruption_ui
from src.ui.emissions_ui import render_emissions_ui
from src.ui.syllabus_workbench import (
    render_simplex_workbench,
    render_artificial_variables_and_duality,
    render_transportation_solver,
    render_assignment_optimizer,
    render_game_theory_studio,
    render_tora_workbench
)
from src.ui.experiments_ui import (
    render_experiments_manager,
    render_saved_models,
    render_documentation_viewer
)

@st.cache_data
def load_application_data() -> pd.DataFrame:
    """Load selected research network or demonstration dataset."""
    path_selected = "data/processed/selected_network.parquet"
    path_flows = "data/processed/freight_flows.parquet"
    path_demo = "data/processed/demo_network.parquet"

    if os.path.exists(path_selected):
        return pd.read_parquet(path_selected)
    elif os.path.exists(path_flows):
        return pd.read_parquet(path_flows).head(5000)
    elif os.path.exists(path_demo):
        return pd.read_parquet(path_demo)
    else:
        from src.data.ingestion import FAF6IngestionPipeline
        pipeline = FAF6IngestionPipeline()
        pipeline.run_pipeline()
        return pd.read_parquet(path_selected)

def main():
    # Load dataset
    try:
        df = load_application_data()
    except Exception as e:
        st.error(f"Error loading freight dataset: {e}")
        return

    # Structured, Humanized Sidebar Navigation
    with st.sidebar:
        # Platform Branding
        st.markdown("""
        <div style="padding: 12px 4px 18px 4px; border-bottom: 1px solid #1E293B; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 22px;">📦</span>
                <div>
                    <h2 style="margin: 0; color: #FFFFFF; font-size: 19px; font-weight: 800; letter-spacing: -0.01em;">
                        OptiChain
                    </h2>
                    <p style="margin: 0; color: #2DD4BF; font-size: 11px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase;">
                        FAF6 Freight Research Platform
                    </p>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <span class="opti-pill opti-pill-slate" style="background:#1E293B; color:#94A3B8; border:1px solid #334155; font-size:10px;">
                    B.Tech Capstone Project
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Primary Workspaces
        workspaces = [
            "Executive Overview & Data",
            "Freight Network Science",
            "Multimodal Optimization & Planning",
            "Disruption Resilience & Stress Testing",
            "Operations Research Syllabus Lab",
            "Research Registry & Reports"
        ]

        workspace_icons = [
            "speedometer2",
            "diagram-3",
            "cpu",
            "exclamation-triangle",
            "calculator",
            "journal-check"
        ]

        ws_override = st.session_state.pop("nav_workspace_override", None)
        selected_workspace = option_menu(
            menu_title="RESEARCH WORKSPACES",
            options=workspaces,
            icons=workspace_icons,
            default_index=0,
            manual_select=ws_override,
            styles={
                "container": {
                    "padding": "6px 8px!important",
                    "background-color": "#FFFFFF",
                    "border-radius": "8px",
                    "border": "1px solid #CBD5E1",
                    "box-shadow": "0 1px 3px rgba(0, 0, 0, 0.06)"
                },
                "menu-title": {
                    "color": "#334155",
                    "font-size": "11px",
                    "font-weight": "800",
                    "letter-spacing": "0.06em",
                    "text-transform": "uppercase",
                    "padding": "4px 4px 6px 6px"
                },
                "icon": {
                    "font-size": "13.5px"
                },
                "nav-link": {
                    "font-size": "12.5px",
                    "font-weight": "600",
                    "text-align": "left",
                    "margin": "3px 0",
                    "padding": "8px 10px",
                    "border-radius": "6px",
                    "color": "#0F172A",
                    "--hover-color": "#F1F5F9"
                },
                "nav-link-selected": {
                    "background-color": "#0D9488",
                    "color": "#FFFFFF!important",
                    "font-weight": "700",
                    "box-shadow": "0 2px 4px rgba(13, 148, 136, 0.25)"
                }
            }
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Active Dataset Status Card
        st.markdown("""
        <div style="background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 12px; font-size: 11px; line-height: 1.5; color: #94A3B8;">
            <div style="font-weight: 700; color: #FFFFFF; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#10B981;"></span>
                Active Research Dataset
            </div>
            <b>Benchmark:</b> FAF6.0 (2022 Release)<br>
            <b>Published by:</b> US BTS & FHWA<br>
            <b>Subnetwork:</b> 3,911 Links (Top 20 Hubs)<br>
            <b>Linear Solver:</b> SciPy HiGHS Active
        </div>
        """, unsafe_allow_html=True)

    # Workspace Sub-Navigation & Content Dispatcher
    if selected_workspace == "Executive Overview & Data":
        sub_tab = st.segmented_control(
            "Overview Navigation:",
            ["National Freight Overview", "FAF6 Flow Explorer", "Data Sources & Provenance"],
            default="National Freight Overview",
            label_visibility="collapsed"
        )
        if not sub_tab or sub_tab == "National Freight Overview":
            render_executive_dashboard(df)
        elif sub_tab == "FAF6 Flow Explorer":
            render_dataset_explorer(df, view_type="explorer")
        elif sub_tab == "Data Sources & Provenance":
            render_dataset_explorer(df, view_type="provenance")

    elif selected_workspace == "Freight Network Science":
        sub_tab = st.segmented_control(
            "Network Navigation:",
            ["Network Connectivity & Centrality", "Corridor Volume & Value Rankings"],
            default="Network Connectivity & Centrality",
            label_visibility="collapsed"
        )
        if not sub_tab or sub_tab == "Network Connectivity & Centrality":
            render_freight_network(df, view_mode="network")
        elif sub_tab == "Corridor Volume & Value Rankings":
            render_freight_network(df, view_mode="corridors")

    elif selected_workspace == "Multimodal Optimization & Planning":
        sub_tab = st.segmented_control(
            "Optimization Navigation:",
            ["Multimodal Freight Allocation (LP)", "Capacity Bottlenecks & Shadow Prices", "Green Freight & Carbon Abatement"],
            default="Multimodal Freight Allocation (LP)",
            label_visibility="collapsed"
        )
        if not sub_tab or sub_tab == "Multimodal Freight Allocation (LP)":
            render_optimizer_ui(df, view_mode="optimizer")
        elif sub_tab == "Capacity Bottlenecks & Shadow Prices":
            render_optimizer_ui(df, view_mode="capacity")
        elif sub_tab == "Green Freight & Carbon Abatement":
            render_emissions_ui(df)

    elif selected_workspace == "Disruption Resilience & Stress Testing":
        sub_tab = st.segmented_control(
            "Resilience Navigation:",
            ["Real-World Disruption Scenarios", "Resilience & Sensitivity Analysis"],
            default="Real-World Disruption Scenarios",
            label_visibility="collapsed"
        )
        if not sub_tab or sub_tab == "Real-World Disruption Scenarios":
            render_disruption_ui(df, view_mode="simulator")
        elif sub_tab == "Resilience & Sensitivity Analysis":
            render_disruption_ui(df, view_mode="comparison")

    elif selected_workspace == "Operations Research Syllabus Lab":
        sub_tab = st.segmented_control(
            "Syllabus Lab Navigation:",
            [
                "Unit I: Simplex Stepper",
                "Unit II: Two-Phase & Duality",
                "Unit III: Transportation & MODI",
                "Unit IV: Hungarian Assignment",
                "Unit IV: Game Theory & Risk",
                "TORA Verification Reports"
            ],
            default="Unit I: Simplex Stepper",
            label_visibility="collapsed"
        )
        if not sub_tab or sub_tab == "Unit I: Simplex Stepper":
            render_simplex_workbench()
        elif sub_tab == "Unit II: Two-Phase & Duality":
            render_artificial_variables_and_duality()
        elif sub_tab == "Unit III: Transportation & MODI":
            render_transportation_solver()
        elif sub_tab == "Unit IV: Hungarian Assignment":
            render_assignment_optimizer()
        elif sub_tab == "Unit IV: Game Theory & Risk":
            render_game_theory_studio()
        elif sub_tab == "TORA Verification Reports":
            render_tora_workbench()

    elif selected_workspace == "Research Registry & Reports":
        sub_tab = st.segmented_control(
            "Registry Navigation:",
            ["Experiment Battery (E1 to E10)", "Saved Scenarios & PDF Generator", "Academic Compendium & Notes"],
            default="Experiment Battery (E1 to E10)",
            label_visibility="collapsed"
        )
        if not sub_tab or sub_tab == "Experiment Battery (E1 to E10)":
            render_experiments_manager()
        elif sub_tab == "Saved Scenarios & PDF Generator":
            render_saved_models()
        elif sub_tab == "Academic Compendium & Notes":
            render_documentation_viewer()

if __name__ == "__main__":
    main()
