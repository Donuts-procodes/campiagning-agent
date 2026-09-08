from __future__ import annotations

import logging

from src.connectors.adapters.email_adapter import EmailAdapter
from src.connectors.adapters.linkedin_adapter import LinkedInAdapter
from src.connectors.adapters.media_adapter import MediaAdapter
from src.models.campaign_state import CampaignState, ExecutionReceiptState

logger = logging.getLogger(__name__)

async def outreach_dispatcher(state: CampaignState) -> dict:
    hitl = state.get("hitl")
    if not hitl or hitl.review_status != "approved" or not hitl.approved_variant_id:
        return {"current_node": "outreach_dispatcher", "error": "No approved variant found"}

    variant_id = hitl.approved_variant_id
    strategy = state.get("strategy")
    creatives = state.get("creatives")

    if not strategy or not creatives:
        return {"current_node": "outreach_dispatcher", "error": "Missing strategy or creatives"}

    variant = next((v for v in strategy.strategy_variants if v.variant_id == variant_id), None)
    bundle = creatives.variant_creatives.get(variant_id)

    if not variant or not bundle:
        return {"current_node": "outreach_dispatcher", "error": "Variant data missing"}

    # Default to task_queue mode for real dispatches
    mode = "task_queue"
    receipts = []

    if bundle.email_sequences:
        adapter = EmailAdapter()
        receipt = adapter.dispatch(mode, {"volume": variant.required_contact_volume, "bundle": bundle.model_dump()})
        receipts.append(receipt)
        
    if bundle.linkedin_scripts:
        adapter = LinkedInAdapter()
        receipt = adapter.dispatch(mode, {"volume": int(variant.required_contact_volume * 0.5), "bundle": bundle.model_dump()})
        receipts.append(receipt)

    # Media Execution (Meta, Google, Inbound Forms)
    if bundle.ad_creatives or bundle.inbound_forms:
        media_adapter = MediaAdapter()
        receipt = media_adapter.dispatch(
            mode,
            {
                "volume": variant.required_contact_volume,
                "ad_creatives": [a.model_dump() for a in bundle.ad_creatives],
                "inbound_forms": [f.model_dump() for f in bundle.inbound_forms],
            }
        )
        receipts.append(receipt)

    return {
        "execution": ExecutionReceiptState(receipts=receipts),
        "current_node": "outreach_dispatcher"
    }
