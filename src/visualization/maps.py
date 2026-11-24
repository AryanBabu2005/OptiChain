"""
Geographic Freight Flow Maps using Plotly.
Visualizes regional freight nodes and multimodal flow corridors across the United States.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import plotly.graph_objects as go
import pandas as pd
from src.network.geography import FAF6_DOMESTIC_ZONES, FAF6_MODES
from src.data.sctg_codes import get_sctg_description, get_sctg_code_str

# Visual theme colors
COLOR_NAVY = "#0F172A"
COLOR_TEAL = "#0D9488"
COLOR_ACCENT = "#3B82F6"
COLOR_BG = "#F8FAFC"
FONT_FAMILY = "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"

MODE_COLORS: Dict[int, str] = {
    1: "#2563EB",  # Truck - Blue
    2: "#DC2626",  # Rail - Red
    3: "#0284C7",  # Water - Cyan/Ocean
    4: "#F59E0B",  # Air - Amber
    5: "#7C3AED",  # Multiple Modes & Mail - Purple
    6: "#059669",  # Pipeline - Emerald
    7: "#64748B",  # Other & Unknown - Slate
    8: "#94A3B8"   # No domestic mode
}

MODE_DISPLAY_NAMES: Dict[int, str] = {
    1: "Truck",
    2: "Rail",
    3: "Water",
    4: "Air",
    5: "Multiple Modes & Mail",
    6: "Pipeline",
    7: "Other & Unknown"
}

FLOW_DISCLAIMER: str = (
    "Lines represent aggregated origin-to-destination freight flows between FAF region representative points. "
    "They do not represent actual road, railway or shipping routes."
)

def create_freight_network_map(
    flows_df: pd.DataFrame,
    max_corridors: int = 35,
    selected_mode: Optional[int] = None,
    selected_commodity: Optional[int] = None,
    return_corridors: bool = False
) -> Union[go.Figure, Tuple[go.Figure, pd.DataFrame]]:
    """
    Generate an interactive Plotly map of the US freight network.
    Renders FAF region representative points and top flow corridors.
    Strictly ranks corridors by actual freight tonnage.
    """
    df = flows_df.copy()

    # Apply transportation mode filter if specified
    if selected_mode is not None and selected_mode > 0:
        df = df[df["dms_mode"] == selected_mode]

    # Apply commodity filter if specified
    if selected_commodity is not None and selected_commodity > 0:
        df = df[df["sctg2"] == selected_commodity]

    # Aggregate flows by corridor, strictly ranked by annual freight tonnage (tons_2022)
    corridors = df.groupby(
        ["dms_orig", "dms_dest", "orig_name", "dest_name", "dms_mode"],
        as_index=False
    ).agg({
        "tons_2022": "sum",
        "value_2022": "sum",
        "distance_miles": "mean"
    }).sort_values(by="tons_2022", ascending=False).head(max_corridors).reset_index(drop=True)

    fig = go.Figure()

    # Add visible legend placeholder traces for transportation modes
    for m_id, m_name in MODE_DISPLAY_NAMES.items():
        m_color = MODE_COLORS.get(m_id, "#64748B")
        fig.add_trace(go.Scattergeo(
            lon=[None], lat=[None],
            mode="lines",
            line=dict(width=3, color=m_color),
            name=m_name,
            showlegend=True
        ))

    # 1. Add Corridor Desire Lines
    max_tons_val = corridors["tons_2022"].max() if len(corridors) > 0 and corridors["tons_2022"].max() > 0 else 1.0

    for _, row in corridors.iterrows():
        orig = int(row["dms_orig"])
        dest = int(row["dms_dest"])
        z_orig = FAF6_DOMESTIC_ZONES.get(orig)
        z_dest = FAF6_DOMESTIC_ZONES.get(dest)

        if not z_orig or not z_dest:
            continue

        mode_id = int(row["dms_mode"])
        line_color = MODE_COLORS.get(mode_id, "#64748B")
        mode_label = MODE_DISPLAY_NAMES.get(mode_id, FAF6_MODES.get(mode_id, f"Mode {mode_id}"))

        # Line width scaled proportionally by actual freight tonnage
        width = max(1.5, min(8.5, (row["tons_2022"] / max_tons_val) * 7.5))

        # Build informative line tooltip
        tooltip_lines = [
            f"<b>Origin FAF Region:</b> {row['orig_name']} (FAF {orig})",
            f"<b>Destination FAF Region:</b> {row['dest_name']} (FAF {dest})",
            f"<b>Transportation Mode:</b> {mode_label}",
            f"<b>Annual Freight Tonnage:</b> {row['tons_2022']:,.1f} thousand short tons"
        ]

        # Add commodity description and code when a commodity filter is selected
        if selected_commodity is not None and selected_commodity > 0:
            comm_desc = get_sctg_description(selected_commodity)
            comm_code = get_sctg_code_str(selected_commodity)
            tooltip_lines.append(f"<b>Commodity:</b> {comm_desc} ({comm_code})")
        else:
            tooltip_lines.append("<b>Commodity Scope:</b> Aggregated Multimodal Volume (All SCTG Commodities)")

        # Freight value when available
        if pd.notna(row.get("value_2022")) and row["value_2022"] > 0:
            tooltip_lines.append(f"<b>Freight Value:</b> ${row['value_2022']:,.1f} Million (Constant 2022 USD)")

        if pd.notna(row.get("distance_miles")) and row["distance_miles"] > 0:
            tooltip_lines.append(f"<b>Routing Distance:</b> {row['distance_miles']:,.0f} miles (Circuity-Adjusted)")

        tooltip_lines.append("<i>Desire line connecting FAF regional representative points (not physical road/rail track).</i>")

        hover_text = "<br>".join(tooltip_lines)

        fig.add_trace(go.Scattergeo(
            locationmode="USA-states",
            lon=[z_orig["lon"], z_dest["lon"]],
            lat=[z_orig["lat"], z_dest["lat"]],
            mode="lines",
            line=dict(width=width, color=line_color),
            opacity=0.70,
            hoverinfo="text",
            text=hover_text,
            showlegend=False
        ))

    # 2. Add Regional Node Markers (FAF Regions - Representative Points)
    unique_zones = set(corridors["dms_orig"]).union(set(corridors["dms_dest"]))
    node_lats, node_lons, node_names, node_tons = [], [], [], []

    # Calculate total regional throughput from the active corridor subset
    node_throughput: Dict[int, float] = {}
    for _, row in corridors.iterrows():
        orig_code = int(row["dms_orig"])
        dest_code = int(row["dms_dest"])
        node_throughput[orig_code] = node_throughput.get(orig_code, 0.0) + row["tons_2022"]
        node_throughput[dest_code] = node_throughput.get(dest_code, 0.0) + row["tons_2022"]

    for z_id in unique_zones:
        z = FAF6_DOMESTIC_ZONES.get(int(z_id))
        if z:
            node_lats.append(z["lat"])
            node_lons.append(z["lon"])
            node_names.append(
                f"<b>FAF Region (Representative Point):</b> {z['name']} ({z['state']})<br>"
                f"<b>FAF Zone Identifier:</b> FAF {z_id}<br>"
                f"<b>Representative Centroid:</b> {z['lat']:.4f}° N, {abs(z['lon']):.4f}° W<br>"
                f"<b>Classification:</b> FAF geographical zone centroid (not a physical logistics terminal)<br>"
                f"<b>Annual Regional Throughput:</b> {node_throughput.get(z_id, 0.0):,.1f} thousand short tons"
            )
            node_tons.append(node_throughput.get(z_id, 10.0))

    if node_tons:
        max_ton = max(node_tons) if max(node_tons) > 0 else 1.0
        sizes = [max(8, min(24, (t / max_ton) * 22)) for t in node_tons]
    else:
        sizes = [10] * len(node_lats)

    fig.add_trace(go.Scattergeo(
        locationmode="USA-states",
        lon=node_lons,
        lat=node_lats,
        mode="markers+text",
        text=[FAF6_DOMESTIC_ZONES[z]["state"] for z in unique_zones if z in FAF6_DOMESTIC_ZONES],
        textposition="top center",
        marker=dict(
            size=sizes,
            color=COLOR_TEAL,
            line=dict(width=1.5, color="#FFFFFF"),
            opacity=0.92
        ),
        hoverinfo="text",
        hovertext=node_names,
        name="FAF Regions (Representative Points)",
        showlegend=True
    ))

    # Layout configuration with disclaimer and visible legend
    fig.update_layout(
        title=dict(
            text="<b>Geographic Freight Desire Lines (FAF6 2022)</b>",
            x=0.02,
            font=dict(size=16, color=COLOR_NAVY, family=FONT_FAMILY)
        ),
        geo=dict(
            scope="usa",
            projection_type="albers usa",
            showland=True,
            landcolor="#F8FAFC",
            subunitcolor="#E2E8F0",
            countrycolor="#94A3B8",
            showlakes=True,
            lakecolor="#F1F5F9"
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.14,
            xanchor="center",
            x=0.5,
            font=dict(size=10.5, family=FONT_FAMILY, color=COLOR_NAVY),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E2E8F0",
            borderwidth=1
        ),
        annotations=[
            dict(
                x=0.5, y=-0.22, xref="paper", yref="paper",
                text=f"<i>{FLOW_DISCLAIMER}</i>",
                showarrow=False,
                font=dict(size=10, color="#64748B", family=FONT_FAMILY),
                align="center"
            )
        ],
        margin=dict(l=10, r=10, t=50, b=75),
        height=620,
        paper_bgcolor="rgba(0,0,0,0)"
    )

    if return_corridors:
        return fig, corridors
    return fig
