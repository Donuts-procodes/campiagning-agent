from src.pipelines.campaign_graph import build_graph


class TestGraphStructure:
    def test_graph_builds_without_error(self):
        graph = build_graph()
        assert graph is not None

    def test_graph_compiles_without_checkpointer(self):
        graph = build_graph()
        compiled = graph.compile(interrupt_before=["hitl_approval_node"])
        assert compiled is not None

    def test_graph_has_all_nodes(self):
        graph = build_graph()
        node_names = set(graph.nodes.keys())
        expected = {
            "icp_enrichment",
            "cold_email_planner",
            "social_planner",
            "abm_planner",
            "pr_planner",
            "partner_planner",
            "content_planner",
            "retention_planner",
            "multi_channel_planner",
            "email_generator",
            "social_generator",
            "compliance_checker",
            "hitl_approval_node",
            "outreach_dispatcher",
        }
        assert expected.issubset(node_names)
