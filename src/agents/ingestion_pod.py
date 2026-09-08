from __future__ import annotations

import logging
import uuid
from typing import Any

from langchain_core.runnables import RunnableConfig

from src.models.campaign_state import AnalysisState, CampaignState
from src.services.rag_service import get_grounding_citations, ingest_campaign_knowledge

logger = logging.getLogger(__name__)


async def knowledge_ingestion_agent(
    state: CampaignState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Ingests, chunks, embeds, and stores campaign assets and context in Milvus."""
    user_input = state.get("user_input")
    if not user_input:
        return {"current_node": "knowledge_ingestion"}

    # Resolve campaign / thread ID
    campaign_id = ""
    if config and "configurable" in config:
        campaign_id = config["configurable"].get("thread_id", "")
    if not campaign_id:
        campaign_id = str(uuid.uuid4())

    logger.info(f"Executing knowledge ingestion node for campaign ID: {campaign_id}")

    try:
        # Ingest all docs, case studies, differentiators, and copy templates into Milvus
        chunk_count = await ingest_campaign_knowledge(campaign_id, user_input)
        logger.info(f"Ingested {chunk_count} knowledge chunks into Milvus for campaign {campaign_id}")

        # Fetch baseline grounding citations
        citations = await get_grounding_citations(
            campaign_id=campaign_id,
            query=f"{user_input.product_service} {user_input.value_proposition}",
            top_k=3,
        )

        existing_analysis = state.get("analysis")
        if existing_analysis:
            existing_analysis.grounding_citations = citations
            return {"analysis": existing_analysis, "current_node": "knowledge_ingestion"}
        else:
            new_analysis = AnalysisState(grounding_citations=citations)
            return {"analysis": new_analysis, "current_node": "knowledge_ingestion"}

    except Exception as e:
        logger.error(f"Knowledge ingestion failed for campaign {campaign_id}: {e}")
        return {"current_node": "knowledge_ingestion"}
