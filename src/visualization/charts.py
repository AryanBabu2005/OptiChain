"""
Analytical Charts and Plotly Visualizations for OptiChain.
Grounded in clean, humanized, editorial data design.
"""

from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.network.geography import FAF6_MODES
from src.data.sctg_codes import (
    get_sctg_description,
    get_sctg_code_str,
    get_sctg_display_label,
    SCTG_EXPLANATORY_NOTE
)

# Refined Editorial Color Palette
COLOR_NAVY = "#0F172A"
COLOR_SLATE = "#475569"
COLOR_TEAL = "#0D9488"
COLOR_PRIMARY = "#0D9488"
COLOR_AMBER = "#D97706"
COLOR_RED = "#DC2626"
COLOR_EMERALD = "#059669"
FONT_FAMILY = "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"

def _apply_humanized_layout(fig: go.Figure, title_text: str, height: int = 400) -> go.Figure:
    """Apply consistent, professional, transparent typography and layout."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(size=15, color=COLOR_NAVY, family=FONT_FAMILY),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color=COLOR_SLATE, size=12),
        margin=dict(l=30, r=30, t=55, b=35),
        height=height,
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12,
            font_family=FONT_FAMILY,
            font_color="#FFFFFF"
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        tickfont=dict(size=11, family=FONT_FAMILY)
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        tickfont=dict(size=11, family=FONT_FAMILY)
    )
    return fig

def plot_mode_share(flows_df: pd.DataFrame, metric: str = "tons_2022") -> go.Figure:
    """Donut chart of transportation mode share with informative, precise tooltips."""
    agg = flows_df.groupby("dms_mode", as_index=False)[metric].sum()
    agg["mode_name"] = agg["dms_mode"].map(lambda m: FAF6_MODES.get(m, f"Mode {m}"))
    total_val = float(agg[metric].sum())
    agg["pct"] = (agg[metric] / total_val * 100.0) if total_val > 0 else 0.0

    is_tons = (metric == "tons_2022")
    metric_title = "Tonnage (Thousand Short Tons)" if is_tons else "Freight Value ($ Millions, Constant 2022 USD)"
    unit_str = "thousand short tons" if is_tons else "Million USD (Constant 2022)"

    palette = ["#0D9488", "#D97706", "#7C3AED", "#059669", "#64748B", "#DC2626", "#EA580C", "#94A3B8"]

    fig = go.Figure(data=[go.Pie(
        labels=agg["mode_name"],
        values=agg[metric],
        hole=0.52,
        textinfo="percent",
        textfont=dict(family=FONT_FAMILY, size=12, color="#FFFFFF"),
        customdata=agg[["pct"]].values,
        hovertemplate=(
            "<b>Transportation Mode: %{label}</b><br>"
            f"Exact Freight {('Tonnage' if is_tons else 'Value')}: %{{value:,.1f}} {unit_str}<br>"
            "Exact Modal Share: %{customdata[0]:.2f}%<br>"
            "<extra></extra>"
        ),
        marker=dict(colors=palette, line=dict(color="#FFFFFF", width=2))
    )])

    fig = _apply_humanized_layout(fig, f"Modal Share Distribution ({metric_title})", height=380)
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        )
    )
    return fig

def plot_commodity_distribution(flows_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Horizontal bar chart of top commodities by volume.
    Uses official SCTG commodity descriptions and standardized humanized tooltips.
    """
    # Preserve exact existing aggregation, ranking, and ordering
    agg = flows_df.groupby("sctg2", as_index=False).agg({
        "tons_2022": "sum",
        "value_2022": "sum"
    }).sort_values(by="tons_2022", ascending=True).tail(top_n)

    total_network_tons = float(flows_df["tons_2022"].sum()) if "tons_2022" in flows_df.columns else 1.0

    # Map SCTG codes to full names and formatted labels via reusable data dictionary
    agg["commodity_name"] = agg["sctg2"].apply(get_sctg_description)
    agg["sctg_code_str"] = agg["sctg2"].apply(get_sctg_code_str)
    agg["display_label"] = agg["sctg2"].apply(lambda c: get_sctg_display_label(c, max_line_width=32))
    agg["pct_of_total"] = (agg["tons_2022"] / total_network_tons) * 100.0 if total_network_tons > 0 else 0.0

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg["display_label"],
        x=agg["tons_2022"],
        orientation="h",
        marker=dict(
            color=COLOR_TEAL,
            line=dict(color="#0F766E", width=1)
        ),
        text=[f"{v:,.0f}k" for v in agg["tons_2022"]],
        textposition="outside",
        textfont=dict(family=FONT_FAMILY, size=11, color=COLOR_NAVY),
        customdata=agg[["commodity_name", "sctg_code_str", "pct_of_total"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "SCTG Code: %{customdata[1]}<br>"
            "Exact Freight Tonnage: %{x:,.1f} thousand short tons<br>"
            "Percentage of Total Freight: %{customdata[2]:.2f}%"
            "<extra></extra>"
        ),
        name="Freight Tonnage"
    ))

    title_text = "Top 10 Commodities by Freight Tonnage (Thousand Short Tons)" if top_n == 10 else f"Top {top_n} Commodities by Freight Tonnage (Thousand Short Tons)"
    fig = _apply_humanized_layout(fig, title_text, height=480)
    fig.update_layout(
        xaxis_title="Freight Mass (Thousand Short Tons)",
        yaxis_title="Commodity (SCTG)",
        yaxis=dict(
            automargin=True,
            tickfont=dict(family=FONT_FAMILY, size=10.5, color=COLOR_NAVY)
        ),
        margin=dict(l=10, r=45, t=55, b=35)
    )
    return fig

def plot_value_vs_tonnage(flows_df: pd.DataFrame, sample_size: int = 150) -> go.Figure:
    """Scatter plot of freight economic value vs physical tonnage."""
    sample = flows_df.sample(min(len(flows_df), sample_size), random_state=42).copy()
    sample["mode_name"] = sample["dms_mode"].map(lambda m: FAF6_MODES.get(m, f"Mode {m}"))

    fig = px.scatter(
        sample,
        x="tons_2022",
        y="value_2022",
        color="mode_name",
        size="distance_miles",
        hover_data=["orig_name", "dest_name", "sctg2"],
        labels={
            "tons_2022": "Freight Tonnage (k tons)",
            "value_2022": "Freight Value ($ Millions)",
            "mode_name": "Transport Mode",
            "distance_miles": "Haul Distance (mi)"
        },
        color_discrete_sequence=["#0D9488", "#D97706", "#7C3AED", "#059669", "#DC2626", "#EA580C"]
    )

    fig = _apply_humanized_layout(fig, "Economic Cargo Value vs Physical Tonnage (Sized by Haul Distance)", height=440)
    return fig

def plot_top_corridors(corridors_df: pd.DataFrame, top_n: int = 10, value_col: str = "tons_2022") -> go.Figure:
    """Ranked bar chart of top inter-regional freight corridors."""
    top = corridors_df.head(top_n).copy()
    top["corridor"] = top["orig_name"] + " → " + top["dest_name"]

    # Defensive resolution of column name
    if value_col not in top.columns:
        if "tons_2022" in top.columns:
            value_col = "tons_2022"
        elif "total_tons" in top.columns:
            value_col = "total_tons"
        elif "value_2022" in top.columns:
            value_col = "value_2022"
        elif "total_value" in top.columns:
            value_col = "total_value"

    metric_name = "Volume (Thousand Tons)" if "tons" in value_col else "Value ($ Millions)"
    bar_color = COLOR_TEAL if "tons" in value_col else COLOR_EMERALD

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top["corridor"],
        y=top[value_col],
        marker=dict(color=bar_color, line=dict(color="#0F766E" if "tons" in value_col else "#047857", width=1)),
        text=[f"{v:,.0f}" for v in top[value_col]],
        textposition="outside",
        textfont=dict(family=FONT_FAMILY, size=11, color=COLOR_NAVY)
    ))

    fig = _apply_humanized_layout(fig, f"Top {top_n} Corridors Ranked by {metric_name}", height=420)
    fig.update_layout(
        xaxis_title="Freight Corridor",
        yaxis_title=metric_name,
        xaxis_tickangle=-30,
        margin=dict(l=30, r=30, t=55, b=90)
    )
    return fig

def plot_sankey_multimodal(flows_df: pd.DataFrame, max_links: int = 25,
                           selected_commodity: Optional[Any] = None,
                           selected_mode: Optional[Any] = None) -> go.Figure:
    """
    Sankey flow diagram tracing Origins -> Transportation Modes -> Destinations.
    - Prevents overlapping labels with distinct node identification and clean city labels.
    - Conserves flow strictly across modal layers without double-counting.
    - Provides interactive tooltips with exact tonnage and percentage share.
    - Supports commodity and mode subset filtering.
    """
    df = flows_df.copy()

    # Apply commodity filter if specified
    if selected_commodity is not None and str(selected_commodity).lower() not in ["all", "all commodities", "none", ""]:
        try:
            c_int = int(selected_commodity)
            df = df[df["sctg2"] == c_int]
        except (ValueError, TypeError):
            df = df[df["sctg2"].astype(str) == str(selected_commodity)]

    # Apply mode filter if specified
    if selected_mode is not None and str(selected_mode).lower() not in ["all", "all modes", "none", ""]:
        try:
            m_int = int(selected_mode)
            df = df[df["dms_mode"] == m_int]
        except (ValueError, TypeError):
            pass

    if df.empty or df["tons_2022"].sum() <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No active freight flows match the selected filter criteria.",
            showarrow=False,
            font=dict(size=14, color=COLOR_SLATE, family=FONT_FAMILY)
        )
        return _apply_humanized_layout(fig, "Multimodal Flow Allocation (Filtered)", height=480)

    # Clean short names for origin and destination to prevent overlapping text
    def clean_label(name: str) -> str:
        s = str(name).split(" (")[0]
        s = s.replace(" IL-IN-WI", ", IL").replace(" PA-NJ-DE-MD", ", PA").replace(" MO-IL", ", MO")
        return s.strip()

    # Aggregate by (orig, mode, dest) to select top flow conduits
    corridor_agg = df.groupby(["orig_name", "dms_mode", "dest_name"], as_index=False)["tons_2022"].sum()
    top_corridors = corridor_agg.sort_values(by="tons_2022", ascending=False).head(max_links).copy()

    total_visualized_tons = float(top_corridors["tons_2022"].sum())
    if total_visualized_tons <= 0:
        total_visualized_tons = 1.0

    # Build unique nodes with explicit layer prefixes to avoid duplicate names
    unique_origs = sorted(list(top_corridors["orig_name"].unique()))
    unique_modes = sorted(list(top_corridors["dms_mode"].unique()))
    unique_dests = sorted(list(top_corridors["dest_name"].unique()))

    orig_nodes = [f"[Orig] {clean_label(o)}" for o in unique_origs]
    mode_nodes = [f"[Mode] {FAF6_MODES.get(m, f'Mode {m}')}" for m in unique_modes]
    dest_nodes = [f"[Dest] {clean_label(d)}" for d in unique_dests]

    all_labels = orig_nodes + mode_nodes + dest_nodes
    label_to_id = {label: i for i, label in enumerate(all_labels)}

    # Mode Color definitions (Teal, Amber, Sky, Orange, Purple)
    mode_color_map = {
        1: "#0D9488",  # Truck (Teal)
        2: "#D97706",  # Rail (Amber)
        3: "#0284C7",  # Water (Sky)
        4: "#EA580C",  # Air (Orange)
        5: "#7C3AED",  # Multimodal (Purple)
        6: "#10B981",  # Pipeline (Emerald)
        7: "#64748B",  # Other (Slate)
        8: "#94A3B8"
    }
    mode_rgba_map = {
        1: "rgba(13, 148, 136, 0.40)",
        2: "rgba(217, 119, 6, 0.40)",
        3: "rgba(2, 132, 199, 0.40)",
        4: "rgba(234, 88, 12, 0.40)",
        5: "rgba(124, 58, 237, 0.40)",
        6: "rgba(16, 185, 129, 0.40)",
        7: "rgba(100, 116, 139, 0.40)",
        8: "rgba(148, 163, 184, 0.40)"
    }

    node_colors = []
    # Origin colors (slate navy)
    node_colors.extend(["#334155" for _ in orig_nodes])
    # Mode colors
    node_colors.extend([mode_color_map.get(m, "#0D9488") for m in unique_modes])
    # Destination colors (deep navy)
    node_colors.extend(["#0F172A" for _ in dest_nodes])

    sources, targets, values, link_colors, link_customdata = [], [], [], [], []

    # 1. Layer 1: Origin -> Mode links (conserved flow)
    om_agg = top_corridors.groupby(["orig_name", "dms_mode"], as_index=False)["tons_2022"].sum()
    for _, row in om_agg.iterrows():
        m_id = int(row["dms_mode"])
        m_name = FAF6_MODES.get(m_id, f"Mode {m_id}")
        o_label = f"[Orig] {clean_label(row['orig_name'])}"
        m_label = f"[Mode] {m_name}"
        t_val = float(row["tons_2022"])
        share_pct = (t_val / total_visualized_tons) * 100.0

        sources.append(label_to_id[o_label])
        targets.append(label_to_id[m_label])
        values.append(t_val)
        link_colors.append(mode_rgba_map.get(m_id, "rgba(13, 148, 136, 0.40)"))
        link_customdata.append(share_pct)

    # 2. Layer 2: Mode -> Destination links (conserved flow)
    md_agg = top_corridors.groupby(["dms_mode", "dest_name"], as_index=False)["tons_2022"].sum()
    for _, row in md_agg.iterrows():
        m_id = int(row["dms_mode"])
        m_name = FAF6_MODES.get(m_id, f"Mode {m_id}")
        m_label = f"[Mode] {m_name}"
        d_label = f"[Dest] {clean_label(row['dest_name'])}"
        t_val = float(row["tons_2022"])
        share_pct = (t_val / total_visualized_tons) * 100.0

        sources.append(label_to_id[m_label])
        targets.append(label_to_id[d_label])
        values.append(t_val)
        link_colors.append(mode_rgba_map.get(m_id, "rgba(13, 148, 136, 0.40)"))
        link_customdata.append(share_pct)

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18,
            thickness=20,
            line=dict(color="#CBD5E1", width=1),
            label=all_labels,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>Throughput Volume: <b>%{value:,.1f} thousand tons</b><extra></extra>"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            customdata=link_customdata,
            hovertemplate=(
                "<b>%{source.label} → %{target.label}</b><br>"
                "Freight Tonnage: <b>%{value:,.1f} thousand tons</b><br>"
                "Share of Filtered Flow: <b>%{customdata:.1f}%</b><extra></extra>"
            )
        )
    )])

    title_text = "Multimodal Flow Allocation (Origins → Transportation Modes → Destinations)"
    fig = _apply_humanized_layout(fig, title_text, height=520)
    return fig

def plot_disruption_comparison(baseline_tons: float, disrupted_tons: float,
                               baseline_cost: float, disrupted_cost: float) -> go.Figure:
    """Side-by-side comparison bar chart for disruption resilience impact."""
    categories = ["Freight Served (k tons)", "Modeled Cost ($ Millions)"]
    baseline_vals = [baseline_tons, baseline_cost]
    disrupted_vals = [disrupted_tons, disrupted_cost]

    fig = go.Figure(data=[
        go.Bar(
            name="Baseline Network",
            x=categories,
            y=baseline_vals,
            marker_color="#0D9488",
            text=[f"{v:,.1f}" for v in baseline_vals],
            textposition="outside"
        ),
        go.Bar(
            name="Disrupted (Optimized Response)",
            x=categories,
            y=disrupted_vals,
            marker_color="#DC2626",
            text=[f"{v:,.1f}" for v in disrupted_vals],
            textposition="outside"
        )
    ])

    fig = _apply_humanized_layout(fig, "Resilience Performance: Baseline vs Disrupted Response", height=380)
    fig.update_layout(
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    return fig

def plot_pareto_frontier(pareto_points: List[Dict[str, Any]]) -> go.Figure:
    """Plots the Bi-Objective Pareto Trade-off Curve between Logistics Cost and Carbon Emissions."""
    df = pd.DataFrame(pareto_points)
    if df.empty:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["total_co2e_metric_tons"] / 1000.0,
        y=df["total_logistics_cost"] / 1_000_000.0,
        mode="lines+markers",
        line=dict(color="#0D9488", width=3, shape="spline"),
        marker=dict(
            size=11,
            color=df["alpha_green_weight"],
            colorscale="Viridis",
            colorbar=dict(title="Green Weight (α)", thickness=10),
            showscale=True,
            line=dict(width=1.5, color="#FFFFFF")
        ),
        text=[
            f"<b>{r['policy_label']}</b><br>"
            f"Cost: ${r['total_logistics_cost']/1e6:,.2f}M<br>"
            f"Carbon: {r['total_co2e_metric_tons']/1e3:,.1f}k t CO2e<br>"
            f"Rail Share: {r['rail_share_pct']}% | Truck: {r['truck_share_pct']}%"
            for _, r in df.iterrows()
        ],
        hoverinfo="text",
        name="Pareto Frontier"
    ))

    fig = _apply_humanized_layout(fig, "Bi-Objective Pareto Frontier: Cost ($M) vs Carbon (Thousand t CO2e)", height=440)
    fig.update_layout(
        xaxis_title="Carbon Footprint (Thousand Metric Tons CO2e) [Minimizing →]",
        yaxis_title="Total Logistics Operating Cost ($ Millions) [Minimizing →]"
    )
    return fig

def plot_emissions_breakdown(mode_breakdown_df: pd.DataFrame) -> go.Figure:
    """Bar chart showing total CO2 emissions and emissions intensity by transport mode."""
    df = mode_breakdown_df.copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["mode_name"],
        y=df["co2e_metric_tons"] / 1000.0,
        marker=dict(color=["#DC2626", "#0D9488", "#D97706", "#7C3AED", "#059669", "#64748B"][:len(df)]),
        text=[f"{v:,.1f}k t" for v in (df["co2e_metric_tons"] / 1000.0)],
        textposition="outside",
        textfont=dict(family=FONT_FAMILY, size=11, color=COLOR_NAVY)
    ))

    fig = _apply_humanized_layout(fig, "Scope 3 Carbon Emissions by Transportation Mode (Thousand t CO2e)", height=380)
    fig.update_layout(
        xaxis_title="Transport Mode",
        yaxis_title="Emissions (Thousand Metric Tons CO2e)"
    )
    return fig
