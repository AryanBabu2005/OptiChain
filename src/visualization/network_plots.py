"""
Network Topology Plots for OptiChain.
Visualizes NetworkX graph structure, connectivity, and centrality metrics
with rich node tooltips and explicit edge thickness legends.
"""

from typing import Dict, Any, Optional
import networkx as nx
import plotly.graph_objects as go
import numpy as np

COLOR_NAVY = "#0F172A"
COLOR_SLATE = "#334155"
COLOR_MUTED = "#64748B"
COLOR_TEAL = "#0D9488"
COLOR_AMBER = "#D97706"
FONT_FAMILY = "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"

def plot_network_topology(G: nx.DiGraph, layout_type: str = "spring",
                          max_nodes: int = 30) -> go.Figure:
    """
    Generate an interactive Plotly node-link network diagram from NetworkX graph.
    - Node size: Total annual freight throughput (k tons).
    - Edge thickness: Annual freight corridor volume tiers with explicit legend swatches.
    - Hover tooltips: In/out flow, in/out degree, betweenness centrality, PageRank.
    - Layout: Force-directed Spring, Circular, or Kamada-Kawai topological layouts.
    """
    if len(G) == 0:
        return go.Figure()

    # Subgraph if exceeding max_nodes
    if len(G) > max_nodes:
        top_nodes = sorted(G.nodes(), key=lambda n: G.degree(n, weight="tons"), reverse=True)[:max_nodes]
        H = G.subgraph(top_nodes).copy()
    else:
        H = G.copy()

    # Layout algorithms (pure topological visualizations)
    if layout_type == "circular":
        pos = nx.circular_layout(H)
    elif layout_type == "kamada_kawai":
        pos = nx.kamada_kawai_layout(H, weight="distance")
    else:
        # Default: Force-directed spring layout
        pos = nx.spring_layout(H, seed=42, k=0.45, weight="weight")

    # Classify edges into 3 flow tiers for distinct thickness & clear legend explanation
    all_edge_weights = [d.get("tons", d.get("weight", 1.0)) for _, _, d in H.edges(data=True)]
    if all_edge_weights:
        q_high = np.percentile(all_edge_weights, 85)
        q_med = np.percentile(all_edge_weights, 40)
    else:
        q_high, q_med = 1000.0, 200.0

    edge_tiers = [
        {
            "name": f"High-Volume Trunk Corridors (≥ {q_high:,.0f}k tons)",
            "width": 3.0,
            "color": "rgba(13, 148, 136, 0.70)",  # Teal
            "filter": lambda w: w >= q_high,
            "x": [], "y": []
        },
        {
            "name": f"Secondary Corridors ({q_med:,.0f} – {q_high:,.0f}k tons)",
            "width": 1.7,
            "color": "rgba(100, 116, 139, 0.45)",  # Slate
            "filter": lambda w: q_med <= w < q_high,
            "x": [], "y": []
        },
        {
            "name": f"Feeder Corridors (< {q_med:,.0f}k tons)",
            "width": 0.8,
            "color": "rgba(148, 163, 184, 0.28)",  # Light slate
            "filter": lambda w: w < q_med,
            "x": [], "y": []
        }
    ]

    for u, v, d in H.edges(data=True):
        w = float(d.get("tons", d.get("weight", 1.0)))
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        for tier in edge_tiers:
            if tier["filter"](w):
                tier["x"].extend([x0, x1, None])
                tier["y"].extend([y0, y1, None])
                break

    edge_traces = []
    for tier in edge_tiers:
        if tier["x"]:
            edge_traces.append(go.Scatter(
                x=tier["x"], y=tier["y"],
                line=dict(width=tier["width"], color=tier["color"]),
                hoverinfo="none",
                mode="lines",
                name=tier["name"],
                showlegend=True
            ))

    # Node traces & comprehensive tooltips
    node_x, node_y = [], []
    node_text, node_size, node_color = [], [], []
    node_labels = []

    # Get throughput values for scaling
    throughputs = []
    for node in H.nodes():
        nd = H.nodes[node]
        t = float(nd.get("total_throughput_tons", nd.get("inter_regional_throughput_tons", 1.0)))
        if t <= 0:
            t = float(H.degree(node, weight="tons"))
        throughputs.append(t)

    max_tp = max(throughputs) if throughputs and max(throughputs) > 0 else 1.0
    min_tp = min(throughputs) if throughputs else 0.0

    for node in H.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        nd = H.nodes[node]

        name = nd.get("name", f"Zone {node}")
        state = nd.get("state", "US")
        in_t = float(nd.get("inflow_tons", 0.0))
        out_t = float(nd.get("outflow_tons", 0.0))
        intra_t = float(nd.get("intra_regional_tons", 0.0))
        tp_t = float(nd.get("total_throughput_tons", in_t + out_t + intra_t))
        in_deg = int(nd.get("in_degree", H.in_degree(node)))
        out_deg = int(nd.get("out_degree", H.out_degree(node)))
        b_cent = float(nd.get("betweenness_centrality", 0.0))
        p_rank = float(nd.get("pagerank", 0.0))

        # Scaled marker size (13px to 32px)
        norm_val = (tp_t - min_tp) / (max_tp - min_tp) if max_tp > min_tp else 0.5
        size_val = 13.0 + (norm_val * 19.0)
        node_size.append(size_val)
        node_color.append(tp_t / 1000.0)  # in Millions of tons for color scale
        node_labels.append(state if state else str(node))

        tooltip_html = (
            f"<div style='font-family: {FONT_FAMILY}; padding: 4px;'>"
            f"<b style='font-size: 13px; color: {COLOR_NAVY};'>{name} (FAF Zone {node})</b><br>"
            f"<span style='color: {COLOR_MUTED}; font-size: 11px;'>State: {state}</span><br>"
            f"<hr style='margin: 4px 0; border: none; border-top: 1px solid #CBD5E1;'/>"
            f"<b>Annual Freight Throughput:</b><br>"
            f"• Inflow: <b>{in_t:,.1f}k</b> tons<br>"
            f"• Outflow: <b>{out_t:,.1f}k</b> tons<br>"
            f"• Local Intra-Regional: <b>{intra_t:,.1f}k</b> tons<br>"
            f"• Total Throughput: <b>{tp_t:,.1f}k</b> tons ({(tp_t/1e3):,.2f}M tons)<br>"
            f"<hr style='margin: 4px 0; border: none; border-top: 1px solid #CBD5E1;'/>"
            f"<b>Graph Centrality & Topology:</b><br>"
            f"• In-Degree (Incoming Corridors): <b>{in_deg}</b><br>"
            f"• Out-Degree (Outgoing Corridors): <b>{out_deg}</b><br>"
            f"• Betweenness Centrality: <b>{b_cent:.5f}</b><br>"
            f"• PageRank Structural Prestige: <b>{p_rank:.5f}</b>"
            f"</div>"
        )
        node_text.append(tooltip_html)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        name="FAF Regions (Size ∝ Annual Tonnage Throughput)",
        hoverinfo="text",
        text=node_labels,
        textposition="top center",
        textfont=dict(family=FONT_FAMILY, size=10, color=COLOR_NAVY),
        hovertext=node_text,
        marker=dict(
            showscale=True,
            colorscale=[
                [0.0, "#CCFBF1"],   # Very light teal
                [0.3, "#5EEAD4"],   # Soft teal
                [0.7, "#0D9488"],   # Deep teal
                [1.0, "#0F172A"]    # Navy
            ],
            color=node_color,
            size=node_size,
            colorbar=dict(
                thickness=12,
                title=dict(text="Throughput<br>(Million Tons)", font=dict(family=FONT_FAMILY, size=10, color=COLOR_NAVY)),
                xanchor="left",
                x=1.01,
                tickfont=dict(family=FONT_FAMILY, size=9)
            ),
            line=dict(width=1.8, color="#FFFFFF")
        ),
        showlegend=True
    )

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title=dict(
                text="<b>FAF6 Regional Freight Network Topology & Centrality</b><br>"
                     "<sup style='color: #64748B;'>Node Size: Total Annual Regional Throughput | Edge Thickness: Annual Corridor Flow Volume</sup>",
                font=dict(size=14, color=COLOR_NAVY, family=FONT_FAMILY)
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.08,
                xanchor="center",
                x=0.5,
                font=dict(family=FONT_FAMILY, size=10, color=COLOR_MUTED),
                bgcolor="rgba(255,255,255,0.7)"
            ),
            hovermode="closest",
            margin=dict(b=60, l=20, r=20, t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT_FAMILY),
            height=540
        )
    )
    return fig
