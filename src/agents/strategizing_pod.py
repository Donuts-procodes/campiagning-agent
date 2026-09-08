from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.llm import get_instructor_client
from src.models.campaign_state import (
    CampaignState,
    OutreachVariant,
    StrategyState,
)

logger = logging.getLogger(__name__)

class _OutreachVariantsResponse(BaseModel):
    variants: list[OutreachVariant] = Field(min_length=1, max_length=3)

async def _base_planner(state: CampaignState, role: str, instruction: str) -> dict:
    user_input = state.get("user_input")
    if not user_input:
        return {"error": "Missing user_input"}

    strategy = state.get("strategy") or StrategyState()
    client: Any = get_instructor_client()

    target_roas = user_input.target_roas or 3.0
    target_meetings = user_input.target_meetings or 10
    target_cac = user_input.target_cac or (round(user_input.budget / max(target_meetings, 1), 2) if user_input.budget else 250.0)
    budget_allocation = user_input.budget_allocation or {
        "cold_email": 0.40,
        "linkedin": 0.30,
        "meta_ads": 0.15,
        "google_ads": 0.15,
    }

    closed_loop = state.get("closed_loop")
    feedback = {}
    feedback_section = ""
    if closed_loop and closed_loop.latest_evaluation:
        eval_metrics = closed_loop.latest_evaluation
        feedback = {
            "historical_actual_cac": eval_metrics.actual_cac,
            "historical_actual_roas": eval_metrics.actual_roas,
            "historical_conversion_rate": eval_metrics.conversion_rate,
            "performance_status": eval_metrics.performance_status,
            "recommended_budget": eval_metrics.budget_reallocations,
            "recommendations": eval_metrics.optimization_recommendations,
        }
        if eval_metrics.budget_reallocations:
            budget_allocation = eval_metrics.budget_reallocations
        feedback_section = (
            f"\n\nHISTORICAL PERFORMANCE FEEDBACK (Closed-Loop Learning):\n"
            f"- Historical Actual CAC: ${eval_metrics.actual_cac} (Target: ${eval_metrics.target_cac})\n"
            f"- Historical Actual ROAS: {eval_metrics.actual_roas}x (Target: {eval_metrics.target_roas}x)\n"
            f"- Conversion Rate: {eval_metrics.conversion_rate * 100:.2f}%\n"
            f"- Directives: {'; '.join(eval_metrics.optimization_recommendations[:2])}\n"
        )

    cadence_guardrails = (
        "\n\nCADENCE & SPACING GUARDRAILS:\n"
        "1. Touch Spacing: Never fire multiple aggressive touches on Day 1. Maintain a minimum of 2 business days between outreach steps.\n"
        "2. Multi-Channel Progression: Start with an email or soft profile touch on Day 1 -> LinkedIn connection on Day 3-4 -> Value-add proof follow-up on Day 7-8 -> Soft permission close on Day 12-14.\n"
        "3. Variant Differentiation: Every variant must attack a distinct psychological hook (e.g. Variant 1: Direct Financial ROI; Variant 2: Risk Mitigation & Peer Proof; Variant 3: Speed & Zero Operational Overhead).\n"
        "4. Realistic B2B Metrics: Estimated reply rates must reflect realistic B2B outbound benchmarks (0.02 to 0.08)."
    )

    prompt = (
        f"Campaign Name: {user_input.campaign_name}\n"
        f"Company: {user_input.company_name}\n"
        f"Value Prop: {user_input.value_proposition}\n"
        f"Target ICP: {user_input.target_icp}\n"
        f"Campaign Type: {user_input.campaign_type.value}\n"
        f"Duration: {user_input.duration_days} days\n"
        f"Target ROAS: {target_roas}x\n"
        f"Target CAC: ${target_cac}\n"
        f"{feedback_section}\n"
        f"{instruction}\n"
        f"{cadence_guardrails}\n\n"
        f"Generate distinct variants. Each variant must have a unique 'messaging_angle', "
        f"selected channels, and a specific cadence_timeline."
    )

    try:
        result = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            response_model=_OutreachVariantsResponse,
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": prompt},
            ],
        )

        for variant in result.variants:
            if not variant.target_roas:
                variant.target_roas = target_roas
            if not variant.target_cac:
                variant.target_cac = target_cac
            if not variant.channel_budgets:
                variant.channel_budgets = budget_allocation

        updated = StrategyState(
            target_meetings=target_meetings,
            estimated_reply_rate=0.035,  # default baseline
            required_contact_volume=int(target_meetings / 0.035),
            target_roas=target_roas,
            target_cac=target_cac,
            budget_allocation=budget_allocation,
            historical_roas_cac_feedback=feedback,
            strategy_variants=result.variants,
        )
        return {"strategy": updated}
        
    except Exception as e:
        logger.error(f"Planner failed: {e}")
        return {"error": str(e)}

async def cold_email_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are an elite Cold Email Copywriter and Outbound Campaign Architect. Design sequences optimized for primary inbox deliverability, concise copywriting, and high reply rates.",
        "Design a sequence focusing solely on cold email. Optimize for high deliverability, short punchy subjects, and low-friction calls to action."
    )
    return {**res, "current_node": "cold_email_planner"}

async def social_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are an elite B2B Social Selling and Executive LinkedIn Strategist. Design multi-touch relationship cadences that build trust before pitching.",
        "Design a sequence focusing on LinkedIn profile touchpoints, thoughtful connection requests, and conversational follow-ups."
    )
    return {**res, "current_node": "social_planner"}

async def abm_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are an Enterprise Account-Based Marketing (ABM) Director. Design multi-threaded cadences targeting economic buyers and champions within tier-1 accounts.",
        "Design a highly personalized, account-centric outreach sequence targeting multiple stakeholders within specific enterprise accounts."
    )
    return {**res, "current_node": "abm_planner"}

async def pr_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are a Tech PR and Media Relations Director. Craft compelling narrative hooks for journalists, analysts, and media outlets.",
        "Design an outreach sequence targeting journalists, influencers, and media outlets for a product launch or announcement."
    )
    return {**res, "current_node": "pr_planner"}

async def partner_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are a Global Channel Partnerships and Alliances Director. Design value-first outreach to recruit resellers and integration partners.",
        "Design an outreach sequence focused on recruiting affiliates, resellers, or strategic integration partners."
    )
    return {**res, "current_node": "partner_planner"}

async def content_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are a Content Marketing and Brand Authority Strategist. Design outreach focused on mutual value and thought leadership.",
        "Design an outreach sequence for link building, guest posting, or content promotion."
    )
    return {**res, "current_node": "content_planner"}

async def retention_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are a Customer Success and Expansion Revenue Leader. Craft high-touch relationship messages for retention and upsell.",
        "Design an outreach sequence for customer retention, reactivation, upselling, or gathering case studies."
    )
    return {**res, "current_node": "retention_planner"}

async def multi_channel_planner(state: CampaignState) -> dict:
    res = await _base_planner(
        state,
        "You are a VP of Sales Development and Omni-Channel Outbound Architect. Build cohesive, spaced sequences combining email, LinkedIn, and phone touches without overwhelming the prospect.",
        "Design a multi-channel sequence combining email, LinkedIn, and calls in a cohesive omni-channel flow."
    )
    return {**res, "current_node": "multi_channel_planner"}
