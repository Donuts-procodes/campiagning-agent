from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from src.dependencies.auth import verify_api_key
from src.dependencies.graph import get_graph
from src.models.campaign import APIResponse, HITLDecision
from src.models.campaign_state import UserInputState
from src.services.campaign_service import CampaignService

router = APIRouter()

import logging
logger = logging.getLogger(__name__)

@router.post("/campaigns", response_model=APIResponse)
async def create_campaign(
    user_input: UserInputState,
    background_tasks: BackgroundTasks,
    graph: Any = Depends(get_graph),
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    try:
        logger.info(f"[CAMPAIGN START] Form filled with values: {user_input.model_dump()}")
        data = await CampaignService.create_campaign(user_input, background_tasks, graph)
        logger.info(f"[CAMPAIGN SUCCESS] Pipeline initialized. Thread ID: {data.get('thread_id')}")
        return APIResponse(success=True, data=data)
    except Exception as e:
        logger.error(f"[CAMPAIGN FAILURE] Failed to initialize pipeline: {e}", exc_info=True)
        # We can also raise an HTTPException, but returning APIResponse with success=False works depending on frontend handling
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{thread_id}/state", response_model=APIResponse)
async def get_campaign_state(
    thread_id: str,
    graph: Any = Depends(get_graph),
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    data = await CampaignService.get_state(thread_id, graph)
    return APIResponse(success=True, data=data)

@router.post("/campaigns/{thread_id}/approve", response_model=APIResponse)
async def approve_campaign(
    thread_id: str,
    decision: HITLDecision,
    background_tasks: BackgroundTasks,
    graph: Any = Depends(get_graph),
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    data = await CampaignService.approve_campaign(thread_id, decision, background_tasks, graph)
    return APIResponse(success=True, data=data)

@router.get("/campaigns/{thread_id}/receipts", response_model=APIResponse)
async def get_campaign_receipts(
    thread_id: str,
    graph: Any = Depends(get_graph),
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    data = await CampaignService.get_receipts(thread_id, graph)
    return APIResponse(success=True, data=data)


@router.get("/campaigns/{thread_id}/knowledge", response_model=APIResponse)
async def query_campaign_knowledge_endpoint(
    thread_id: str,
    query: str,
    category: str | None = None,
    top_k: int = 5,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.rag_service import search_campaign_knowledge
    matches = await search_campaign_knowledge(
        campaign_id=thread_id,
        query=query,
        category=category,
        top_k=top_k,
    )
    return APIResponse(success=True, data={"matches": matches, "count": len(matches)})


from pydantic import BaseModel, Field

class CampaignContactCreate(BaseModel):
    name: str
    company_name: str
    email: str
    title: str = "Lead"
    linkedin_url: str = ""
    status: str = "enrolled"
    variant_id: str = "variant1"

class CampaignContactUpdate(BaseModel):
    status: str

@router.get("/campaigns/{thread_id}/crm", response_model=APIResponse)
async def get_campaign_crm_contacts(
    thread_id: str,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.crm_service import CRMService
    contacts = await CRMService.get_campaign_contacts(thread_id)
    # If none enrolled yet, automatically seed sample prospects matching campaign
    if not contacts:
        contacts = await CRMService.seed_campaign_leads(thread_id)
    return APIResponse(success=True, data=contacts)

@router.post("/campaigns/{thread_id}/crm", response_model=APIResponse)
async def add_campaign_crm_contact(
    thread_id: str,
    payload: CampaignContactCreate,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.crm_service import CRMService
    contact = await CRMService.add_campaign_contact(
        campaign_thread_id=thread_id,
        name=payload.name,
        company_name=payload.company_name,
        email=payload.email,
        title=payload.title,
        linkedin_url=payload.linkedin_url,
        variant_id=payload.variant_id,
        status=payload.status,
    )
    return APIResponse(success=True, data=contact)

@router.patch("/campaigns/{thread_id}/crm/{contact_id}", response_model=APIResponse)
async def update_campaign_crm_contact_status(
    thread_id: str,
    contact_id: str,
    payload: CampaignContactUpdate,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.crm_service import CRMService
    success = await CRMService.update_campaign_contact_status(
        campaign_thread_id=thread_id,
        contact_id=contact_id,
        status=payload.status,
    )
    return APIResponse(success=success, data={"contact_id": contact_id, "status": payload.status})

@router.post("/campaigns/{thread_id}/crm/seed", response_model=APIResponse)
async def seed_campaign_crm_contacts(
    thread_id: str,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.crm_service import CRMService
    contacts = await CRMService.seed_campaign_leads(thread_id)
    return APIResponse(success=True, data=contacts)

class BulkContactsPayload(BaseModel):
    contacts: list[CampaignContactCreate]

class AutoSourcePayload(BaseModel):
    company_name: str | None = None
    target_icp: str | None = None
    target_geography: str = "North America"
    count: int = 5

@router.post("/campaigns/{thread_id}/crm/bulk", response_model=APIResponse)
async def bulk_enroll_crm_contacts(
    thread_id: str,
    payload: BulkContactsPayload,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.crm_service import CRMService
    contacts_data = [c.model_dump() for c in payload.contacts]
    results = await CRMService.bulk_enroll_contacts(thread_id, contacts_data)
    return APIResponse(success=True, data={"enrolled_count": len(results), "contacts": results})

@router.post("/campaigns/{thread_id}/crm/auto-source", response_model=APIResponse)
async def auto_source_crm_contacts(
    thread_id: str,
    payload: AutoSourcePayload,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    from src.services.crm_service import CRMService
    results = await CRMService.autonomous_prospect_sourcing(
        campaign_thread_id=thread_id,
        company_name=payload.company_name or "Target",
        target_icp=payload.target_icp or "VP Infrastructure, Head of DevOps",
        target_geography=payload.target_geography,
        count=payload.count,
    )
    return APIResponse(success=True, data={"sourced_count": len(results), "contacts": results})


# ==========================================
# Midstream: Inbound Data Collection (jj.mmd Stage 2 -> 3)
# ==========================================

class InboundWebhookPayload(BaseModel):
    name: str
    company_name: str
    email: str
    title: str = "Lead"
    linkedin_url: str = ""
    attribution_source: str = "meta_ads"  # meta_ads, google_ads, web_form, demo_request
    ad_id: str | None = None
    form_id: str | None = None
    utm_tags: dict[str, str] = Field(default_factory=dict)
    deal_value: float = 0.0
    status: str = "new"
    variant_id: str = "variant1"


class DemoRequestPayload(BaseModel):
    name: str
    company_name: str
    email: str
    title: str = "Decision Maker"
    notes: str = ""
    utm_tags: dict[str, str] = Field(default_factory=dict)
    deal_value: float = 3500.0


@router.post("/campaigns/{thread_id}/inbound/webhook", response_model=APIResponse)
async def inbound_lead_webhook(
    thread_id: str,
    payload: InboundWebhookPayload,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    """
    Midstream Inbound Data Collection:
    Captures prospects from Web Forms, Ad Conversions, and Webhooks,
    attributing ad_id, form_id, and UTM parameters into the Downstream CRM.
    """
    from src.services.crm_service import CRMService
    contact = await CRMService.add_campaign_contact(
        campaign_thread_id=thread_id,
        name=payload.name,
        company_name=payload.company_name,
        email=payload.email,
        title=payload.title,
        linkedin_url=payload.linkedin_url,
        variant_id=payload.variant_id,
        status=payload.status,
        attribution_source=payload.attribution_source,
        ad_id=payload.ad_id,
        form_id=payload.form_id,
        utm_tags=payload.utm_tags,
        deal_value=payload.deal_value,
    )
    return APIResponse(success=True, data=contact)


@router.post("/campaigns/{thread_id}/inbound/demo-request", response_model=APIResponse)
async def inbound_demo_request(
    thread_id: str,
    payload: DemoRequestPayload,
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    """
    Midstream Inbound Demo Request:
    Direct high-intent capture route transitioning prospects straight to 'qualified'.
    """
    from src.services.crm_service import CRMService
    contact = await CRMService.add_campaign_contact(
        campaign_thread_id=thread_id,
        name=payload.name,
        company_name=payload.company_name,
        email=payload.email,
        title=payload.title,
        status="qualified",
        attribution_source="demo_request",
        utm_tags=payload.utm_tags,
        deal_value=payload.deal_value,
    )
    return APIResponse(success=True, data=contact)


# ==========================================
# Feedback Loop: Closed-Loop Learning (jj.mmd FeedbackLoop)
# ==========================================

@router.get("/campaigns/{thread_id}/feedback-loop", response_model=APIResponse)
async def get_feedback_loop_metrics(
    thread_id: str,
    graph: Any = Depends(get_graph),
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    """
    Closed-Loop Learning Evaluation:
    Computes actual CAC, Conversion Rates, ROAS vs targets, and generates optimization directives.
    """
    from src.services.learning_service import LearningService
    metrics = await LearningService.evaluate_campaign_performance(thread_id, graph=graph)
    return APIResponse(success=True, data=metrics.model_dump())


@router.post("/campaigns/{thread_id}/feedback-loop/apply", response_model=APIResponse)
async def apply_feedback_loop(
    thread_id: str,
    graph: Any = Depends(get_graph),
    api_key: str = Depends(verify_api_key),
) -> APIResponse:
    """
    Closed-Loop Feedback Application:
    Injects evaluated historical ROAS/CAC data and budget reallocations back into the LangGraph state.
    """
    from src.services.learning_service import LearningService
    result = await LearningService.apply_feedback_to_campaign(thread_id, graph=graph)
    return APIResponse(success=True, data=result)




