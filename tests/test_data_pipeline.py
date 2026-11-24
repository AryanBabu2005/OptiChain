"""
Automated Data Ingestion and Model Integration Tests for OptiChain.
"""

import os
import pytest
import pandas as pd
import numpy as np
from src.data.validation import FAF6DataValidator
from src.data.provenance import DataProvenanceTracker
from src.models.freight_model import MultimodalFreightModel
from src.models.capacity_model import CapacityPlanningModel
from src.models.disruption_model import FreightDisruptionSimulator
from src.optimization.verification import SolverVerificationEngine

class TestDataPipeline:
    def test_raw_files_and_provenance(self):
        tracker = DataProvenanceTracker()
        prov = tracker.get_source_provenance()
        assert prov["benchmark_year"] == 2022
        assert prov["sources"]["raw_csv"]["exists"] is True
        assert len(prov["sources"]["raw_csv"]["sha256"]) == 64

    def test_cleaned_parquet_validity(self):
        parquet_path = "data/processed/selected_network.parquet"
        assert os.path.exists(parquet_path), "selected_network.parquet does not exist"
        df = pd.read_parquet(parquet_path)
        assert len(df) > 0

        val = FAF6DataValidator()
        res = val.validate_dataset(df)
        assert res["passed"] is True
        assert res["statistics"]["negative_tons_count"] == 0
        assert res["statistics"]["negative_value_count"] == 0

    def test_demonstration_dataset(self):
        demo_path = "data/processed/demo_network.parquet"
        assert os.path.exists(demo_path)
        df_demo = pd.read_parquet(demo_path)
        assert len(df_demo) > 0
        assert "is_demonstration" in df_demo.columns

class TestModelIntegration:
    @pytest.fixture
    def demo_df(self):
        return pd.read_parquet("data/processed/demo_network.parquet")

    def test_freight_optimizer_run(self, demo_df):
        model = MultimodalFreightModel()
        res = model.build_and_solve(demo_df, capacity_multiplier=1.2, supply_slack_factor=1.2)
        assert res["status"] == "optimal"
        assert res["objective_value"] > 0
        assert res["num_decision_vars"] > 0
        assert len(res["allocations_df"]) > 0

        # Verification of enhanced post-optimization outputs
        assert "demand_df" in res and len(res["demand_df"]) > 0
        assert "supply_df" in res and len(res["supply_df"]) > 0
        assert "capacity_df" in res and len(res["capacity_df"]) > 0
        assert "binding_corridors_df" in res
        assert "commodity_name" in res["allocations_df"].columns
        assert res["demand_satisfaction_pct"] == 100.0

        # Infeasibility diagnostic verification
        infeas_res = model.build_and_solve(demo_df, capacity_multiplier=0.7, supply_slack_factor=0.7)
        assert infeas_res["status"] == "infeasible"
        assert len(infeas_res["infeasibility_reasons"]) > 0

    def test_capacity_expansion_run(self, demo_df):
        cap_model = CapacityPlanningModel()
        res = cap_model.plan_capacity(demo_df)
        assert res["status"] == "optimal"
        assert res["total_objective"] > 0

    def test_disruption_simulator_run(self, demo_df):
        sim = FreightDisruptionSimulator()
        res = sim.simulate_disruption(demo_df, capacity_retention=0.5)
        assert res["status"] == "optimal"
        assert res["resilience_service_ratio"] <= 100.0

    def test_solver_verification_engine(self):
        # Verify custom simplex against SciPy
        c = np.array([3.0, 2.0])
        A = np.array([[1.0, 1.0], [2.0, 1.0]])
        b = np.array([4.0, 5.0])
        verif = SolverVerificationEngine.verify_simplex_solution(c, A, b, maximize=True)
        assert verif["verified"] is True
        assert verif["custom_status"] == "optimal"

class TestCommodityVisualization:
    def test_sctg_codes_and_descriptions(self):
        from src.data.sctg_codes import SCTG_DESCRIPTIONS, get_sctg_description, get_sctg_code_str

        expected_codes = {
            2: "Cereal grains (includes seed)",
            7: "Other prepared foodstuffs, fats and oils",
            11: "Natural sands",
            12: "Gravel and crushed stone",
            17: "Gasoline and aviation turbine fuel",
            18: "Fuel oils",
            19: "Other coal and petroleum products, not elsewhere classified",
            20: "Basic chemicals",
            31: "Non-metallic mineral products",
            41: "Waste and scrap"
        }

        for code, expected_name in expected_codes.items():
            assert SCTG_DESCRIPTIONS[code] == expected_name
            assert get_sctg_description(code) == expected_name
            assert get_sctg_code_str(code) == f"SCTG {code:02d}"

    def test_plot_commodity_distribution_integrity(self):
        from src.visualization.charts import plot_commodity_distribution, COLOR_TEAL
        from src.data.sctg_codes import SCTG_EXPLANATORY_NOTE

        df = pd.read_parquet("data/processed/selected_network.parquet")
        fig = plot_commodity_distribution(df, top_n=10)

        # 1. Title verification
        assert "Top 10 Commodities by Freight Tonnage (Thousand Short Tons)" in fig.layout.title.text

        # 2. Number of bars
        trace = fig.data[0]
        assert len(trace.x) == 10
        assert len(trace.y) == 10

        # 3. Bar color verification (must be teal, not blue)
        assert trace.marker.color == COLOR_TEAL

        # 4. Underlying data preservation
        raw_top10 = df.groupby("sctg2")["tons_2022"].sum().sort_values().tail(10)
        assert np.allclose(trace.x, raw_top10.values)

        # 5. Tooltip customdata verification
        # customdata has [commodity_name, sctg_code_str, pct_of_total]
        assert trace.customdata.shape == (10, 3)
        assert "%{customdata[0]}" in trace.hovertemplate
        assert "%{customdata[1]}" in trace.hovertemplate
        assert "%{x:,.1f}" in trace.hovertemplate
        assert "%{customdata[2]:.2f}%" in trace.hovertemplate

        # 6. Explanatory note verification
        assert "Standard Classification of Transported Goods (SCTG)" in SCTG_EXPLANATORY_NOTE

    def test_geographic_freight_desire_lines_map(self):
        from src.visualization.maps import create_freight_network_map, FLOW_DISCLAIMER
        from src.network.geography import FAF6_DOMESTIC_ZONES

        df = pd.read_parquet("data/processed/selected_network.parquet")

        # 1. Test basic call and return_corridors=True
        fig, corridors_df = create_freight_network_map(df, max_corridors=20, return_corridors=True)

        # 2. Corridors must be ranked descending by freight tonnage
        assert len(corridors_df) == 20
        assert (corridors_df["tons_2022"].diff().dropna() <= 0).all(), "Corridors not ranked descending by tonnage"

        # 3. Node trace must be named 'FAF Regions (Representative Points)'
        node_traces = [t for t in fig.data if t.mode == "markers+text"]
        assert len(node_traces) == 1
        assert node_traces[0].name == "FAF Regions (Representative Points)"

        # 4. Legend must contain mode traces and representative points
        trace_names = [t.name for t in fig.data if t.name]
        assert "Truck" in trace_names
        assert "Rail" in trace_names
        assert "Water" in trace_names
        assert "Air" in trace_names
        assert "Multiple Modes & Mail" in trace_names
        assert "Pipeline" in trace_names
        assert "Other & Unknown" in trace_names
        assert "FAF Regions (Representative Points)" in trace_names

        # 5. Disclaimer verification
        assert FLOW_DISCLAIMER == (
            "Lines represent aggregated origin-to-destination freight flows between FAF region representative points. "
            "They do not represent actual road, railway or shipping routes."
        )
        assert any(FLOW_DISCLAIMER in (ann.text or "") for ann in fig.layout.annotations)

        # 6. Test line tooltips with commodity filter
        fig_comm, _ = create_freight_network_map(df, max_corridors=10, selected_commodity=2, return_corridors=True)
        line_traces = [t for t in fig_comm.data if t.mode == "lines" and t.text]
        assert len(line_traces) > 0
        first_tooltip = line_traces[0].text
        assert "Origin FAF Region:" in first_tooltip
        assert "Destination FAF Region:" in first_tooltip
        assert "Transportation Mode:" in first_tooltip
        assert "Annual Freight Tonnage:" in first_tooltip
        assert "Cereal grains (includes seed)" in first_tooltip
        assert "SCTG 02" in first_tooltip

        # 7. Coordinates verification: all corridor endpoints must exist in FAF6_DOMESTIC_ZONES
        for _, row in corridors_df.iterrows():
            orig_id = int(row["dms_orig"])
            dest_id = int(row["dms_dest"])
            assert orig_id in FAF6_DOMESTIC_ZONES
            assert dest_id in FAF6_DOMESTIC_ZONES
            assert FAF6_DOMESTIC_ZONES[orig_id]["lat"] != 0.0
            assert FAF6_DOMESTIC_ZONES[dest_id]["lon"] != 0.0

    def test_freight_network_graph_and_hhi_analytics(self):
        """Comprehensive verification of Freight Network Graph Analytics & Market Concentration."""
        from src.network.graph_builder import FreightGraphBuilder
        from src.network.network_metrics import FreightNetworkMetrics
        from src.visualization.network_plots import plot_network_topology
        from src.visualization.charts import plot_sankey_multimodal

        df = pd.read_parquet("data/processed/selected_network.parquet")

        # 1. Graph Construction & Self-Loop Verification
        G = FreightGraphBuilder.build_graph_from_flows(df, exclude_self_loops=True)
        assert G.number_of_nodes() == 20, f"Expected 20 regions, got {G.number_of_nodes()}"
        assert G.number_of_edges() == 380, f"Expected 380 inter-regional edges, got {G.number_of_edges()}"
        assert G.graph["total_regions"] == 20
        assert G.graph["active_directed_corridors"] == 380
        assert G.graph["total_corridor_combinations"] == 400
        assert G.graph["intra_regional_zones"] == 20
        assert G.graph["zero_flow_corridors"] == 0

        # Verify edge weights are actual freight tonnage
        for u, v, d in G.edges(data=True):
            assert "tons" in d and d["tons"] > 0
            assert "weight" in d and d["weight"] == d["tons"]

        # 2. Node Metrics Computation
        node_df = FreightNetworkMetrics.compute_node_metrics(G)
        assert len(node_df) == 20
        assert "betweenness_centrality" in node_df.columns
        assert "pagerank" in node_df.columns
        assert "inflow_tons" in node_df.columns
        assert "outflow_tons" in node_df.columns
        assert "intra_regional_tons" in node_df.columns
        assert "total_throughput_tons" in node_df.columns

        # Verify attributes attached back to NetworkX nodes
        first_node = list(G.nodes())[0]
        assert "betweenness_centrality" in G.nodes[first_node]
        assert "pagerank" in G.nodes[first_node]
        assert "inflow_tons" in G.nodes[first_node]

        # 3. HHI Concentration & Underlying Shares Verification
        hhi = FreightNetworkMetrics.compute_concentration_indices(df)
        assert hhi["basis"] == "freight_tonnage"
        assert 7700 < hhi["mode_hhi"] < 7900, f"Unexpected mode HHI: {hhi['mode_hhi']}"
        assert 1400 < hhi["commodity_hhi"] < 1550, f"Unexpected commodity HHI: {hhi['commodity_hhi']}"
        assert hhi["mode_concentration_level"] == "High"
        assert "Low" in hhi["commodity_concentration_level"] or "Diversified" in hhi["commodity_concentration_level"]

        # Underlying shares sum to 100% and squared terms sum to HHI
        mode_shares = hhi["mode_shares_df"]
        assert np.isclose(mode_shares["share_tons_pct"].sum(), 100.0, atol=1e-3)
        assert np.isclose(mode_shares["squared_share_tons"].sum(), hhi["mode_hhi"], atol=1e-1)
        assert "mode_name" in mode_shares.columns

        comm_shares = hhi["commodity_shares_df"]
        assert np.isclose(comm_shares["share_tons_pct"].sum(), 100.0, atol=1e-3)
        assert np.isclose(comm_shares["squared_share_tons"].sum(), hhi["commodity_hhi"], atol=1e-1)
        assert "commodity_name" in comm_shares.columns

        # Value-based HHI verification
        assert "mode_hhi_value" in hhi and hhi["mode_hhi_value"] > 0
        assert "commodity_hhi_value" in hhi and hhi["commodity_hhi_value"] > 0

        # 4. Network Topology Graph Verification
        fig_topo = plot_network_topology(G, layout_type="spring")
        # Must have edge flow tier traces + node trace
        assert len(fig_topo.data) >= 2
        edge_tier_names = [t.name for t in fig_topo.data if t.name and "Corridors" in t.name]
        assert len(edge_tier_names) >= 2, "Explicit edge thickness legend tiers missing"
        node_traces = [t for t in fig_topo.data if t.name and "FAF Regions" in t.name]
        assert len(node_traces) == 1
        # Tooltip content verification
        tooltip_sample = node_traces[0].hovertext[0]
        assert "Betweenness Centrality:" in tooltip_sample
        assert "PageRank Structural Prestige:" in tooltip_sample
        assert "Inflow:" in tooltip_sample
        assert "Outflow:" in tooltip_sample

        # 5. Multimodal Sankey Flow Conservation & Filtering
        fig_sankey = plot_sankey_multimodal(df, max_links=25, selected_commodity=12)
        sankey_trace = fig_sankey.data[0]
        node_labels = sankey_trace.node.label
        assert any(l.startswith("[Orig]") for l in node_labels)
        assert any(l.startswith("[Mode]") for l in node_labels)
        assert any(l.startswith("[Dest]") for l in node_labels)
        # Link hover template includes percentage and tonnage
        assert "%{value:,.1f}" in sankey_trace.link.hovertemplate
        assert "%{customdata:.1f}%" in sankey_trace.link.hovertemplate

        # 6. Top Corridors & Cargo Value vs Carrier Cost Distinction
        top_corr = FreightNetworkMetrics.compute_top_corridors(df, top_n=10, include_mode=True, exclude_intra=True)
        assert len(top_corr) == 10
        assert "carrier_transport_cost_mil" in top_corr.columns
        assert "value_2022" in top_corr.columns
        assert "value_per_ton" in top_corr.columns
        assert "mode_name" in top_corr.columns
        # Carrier transport cost must be positive and distinct from cargo value
        assert (top_corr["carrier_transport_cost_mil"] > 0).all()
        assert not np.array_equal(top_corr["carrier_transport_cost_mil"], top_corr["value_2022"])

