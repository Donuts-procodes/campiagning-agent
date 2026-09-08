from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.llm import get_instructor_client
from src.models.campaign_state import AnalysisState, CampaignState, EnrichedICP

logger = logging.getLogger(__name__)

class _ICPEnrichmentResponse(BaseModel):
    enriched_icps: list[EnrichedICP] = Field(min_length=1, max_length=3)
    sufficiency_score: float = Field(ge=0.0, le=1.0)


async def icp_enrichment_agent(state: CampaignState) -> dict:
    user_input = state.get("user_input")
    if not user_input:
        return {"current_node": "icp_enrichment", "error": "Missing user_input"}

    client: Any = get_instructor_client()

    existing_citations = []
    analysis = state.get("analysis")
    if analysis and analysis.grounding_citations:
        existing_citations = analysis.grounding_citations

    context_snippets = "\n".join([f"- {c.content_snippet}" for c in existing_citations])
    differentiators_text = ", ".join(user_input.differentiators) if user_input.differentiators else "N/A"
    competitors_text = ", ".join(user_input.competitors) if user_input.competitors else "N/A"

    prompt = (
        f"Company: {user_input.company_name}\n"
        f"Product/Service: {user_input.product_service}\n"
        f"Value Proposition: {user_input.value_proposition}\n"
        f"Target ICP: {user_input.target_icp}\n"
        f"Geography: {user_input.target_geography}\n"
        f"Key Differentiators: {differentiators_text}\n"
        f"Buying Trigger Event: {user_input.trigger_event or 'N/A'}\n"
        f"Competitors: {competitors_text}\n\n"
        f"Product & Proof Context:\n{context_snippets or 'N/A'}\n\n"
        f"Based on this base ICP and verified context, generate 1 to 3 enriched ICP segments. "
        f"Include firmographics, specific job titles to target, and their likely pain points."
    )

    system_prompt = (
        "You are an elite Enterprise B2B Market Researcher and Sales Intelligence Architect.\n"
        "Your role is to transform raw product briefs and verified citations into high-resolution ICP segments.\n\n"
        "CORE GUARDRAILS:\n"
        "1. Exact Buying Authorities: Do not use generic job titles. Target concrete decision-makers (e.g. 'VP of Infrastructure', 'Head of Platform Engineering', 'CTO').\n"
        "2. Measurable Operational Pain Points: Avoid vague statements like 'needs efficiency'. Pinpoint explicit technical or financial friction (e.g. 'cloud compute bill overruns', 'kubernetes cluster sprawl', 'slow deployment cycles').\n"
        "3. Grounding Integrity: Ground your analysis strictly in the verified product proof points and differentiators. Never hallucinate unsupported features.\n"
        "4. Bounded Firmographics: Target realistic revenue/employee tiers and company stages appropriate for the pricing tier and geography."
    )

    try:
        result = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            response_model=_ICPEnrichmentResponse,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        
        updated = AnalysisState(
            sufficiency_score=result.sufficiency_score,
            is_sufficient=result.sufficiency_score >= 0.7,
            enriched_icps=result.enriched_icps,
            grounding_citations=existing_citations,
        )
        return {"analysis": updated, "current_node": "icp_enrichment"}
        
    except Exception as e:
        logger.error(f"ICP Enrichment failed: {e}")
        return {"current_node": "icp_enrichment", "error": str(e)}
