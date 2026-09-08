from typing import Any, cast

from langgraph.graph import END, StateGraph

from src.agents.analysis_pod import icp_enrichment_agent
from src.agents.creation_pod import (
    email_sequence_generator,
    media_ad_generator,
    social_outreach_generator,
)
from src.agents.execution_pod import outreach_dispatcher
from src.agents.ingestion_pod import knowledge_ingestion_agent
from src.agents.strategizing_pod import (
    abm_planner,
    cold_email_planner,
    content_planner,
    multi_channel_planner,
    partner_planner,
    pr_planner,
    retention_planner,
    social_planner,
)
from src.agents.verification_pod import compliance_checker
from src.models.campaign_state import CampaignState, CampaignType


def build_graph() -> StateGraph:
    workflow = StateGraph(cast(type[Any], CampaignState))

    # Add Nodes
    workflow.add_node("knowledge_ingestion", knowledge_ingestion_agent)
    workflow.add_node("icp_enrichment", icp_enrichment_agent)
    
    # Planners
    workflow.add_node("cold_email_planner", cold_email_planner)
    workflow.add_node("social_planner", social_planner)
    workflow.add_node("abm_planner", abm_planner)
    workflow.add_node("pr_planner", pr_planner)
    workflow.add_node("partner_planner", partner_planner)
    workflow.add_node("content_planner", content_planner)
    workflow.add_node("retention_planner", retention_planner)
    workflow.add_node("multi_channel_planner", multi_channel_planner)
    
    # Asset Generators (Email, Social Outreach, Media Ads & Inbound Forms)
    workflow.add_node("email_generator", email_sequence_generator)
    workflow.add_node("social_generator", social_outreach_generator)
    workflow.add_node("media_ad_generator", media_ad_generator)
    
    workflow.add_node("compliance_checker", compliance_checker)
    
    # HITL Node
    def hitl_approval_node(state: CampaignState) -> dict:
        return {"current_node": "hitl_approval_node"}
    workflow.add_node("hitl_approval_node", hitl_approval_node)
    
    workflow.add_node("outreach_dispatcher", outreach_dispatcher)

    # Routing: Ingest knowledge into Milvus -> Enrich ICP
    workflow.set_entry_point("knowledge_ingestion")
    workflow.add_edge("knowledge_ingestion", "icp_enrichment")
    
    def planner_router(state: CampaignState):
        user_input = state.get("user_input")
        if not user_input:
            return "multi_channel_planner"
        c_type = user_input.campaign_type
        if c_type == CampaignType.COLD_EMAIL:
            return "cold_email_planner"
        elif c_type == CampaignType.LINKEDIN_OUTREACH:
            return "social_planner"
        elif c_type == CampaignType.ABM:
            return "abm_planner"
        elif c_type == CampaignType.PRODUCT_LAUNCH_PR:
            return "pr_planner"
        elif c_type == CampaignType.PARTNER_AFFILIATE:
            return "partner_planner"
        elif c_type == CampaignType.CONTENT_PROMOTION:
            return "content_planner"
        elif c_type == CampaignType.RETENTION_UPSELL:
            return "retention_planner"
        else:
            return "multi_channel_planner"

    workflow.add_conditional_edges(
        "icp_enrichment",
        planner_router,
        {
            "cold_email_planner": "cold_email_planner",
            "social_planner": "social_planner",
            "abm_planner": "abm_planner",
            "pr_planner": "pr_planner",
            "partner_planner": "partner_planner",
            "content_planner": "content_planner",
            "retention_planner": "retention_planner",
            "multi_channel_planner": "multi_channel_planner",
        }
    )
    
    planners = [
        "cold_email_planner", "social_planner", "abm_planner",
        "pr_planner", "partner_planner", "content_planner",
        "retention_planner", "multi_channel_planner"
    ]
    
    for planner in planners:
        workflow.add_edge(planner, "email_generator")

    workflow.add_edge("email_generator", "social_generator")
    workflow.add_edge("social_generator", "media_ad_generator")
    workflow.add_edge("media_ad_generator", "compliance_checker")
    
    # Compliance check loop
    def compliance_router(state: CampaignState):
        verification = state.get("verification")
        if verification and not verification.all_passed:
            revision_count = state.get("revision_count", 0)
            if revision_count < 3:
                return "email_generator"  # retry generation
        return "hitl_approval_node"

    workflow.add_conditional_edges(
        "compliance_checker",
        compliance_router,
        {
            "email_generator": "email_generator",
            "hitl_approval_node": "hitl_approval_node"
        }
    )

    # Resume after approval
    def approval_router(state: CampaignState):
        hitl = state.get("hitl")
        if hitl and hitl.review_status == "approved":
            return "outreach_dispatcher"
        return END

    workflow.add_conditional_edges(
        "hitl_approval_node",
        approval_router,
        {
            "outreach_dispatcher": "outreach_dispatcher",
            END: END
        }
    )

    workflow.add_edge("outreach_dispatcher", END)

    return workflow


def compile_graph(checkpointer=None):
    workflow = build_graph()
    return workflow.compile(checkpointer=checkpointer)
