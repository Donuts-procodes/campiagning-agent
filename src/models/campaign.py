from typing import Any

from pydantic import BaseModel, Field


class CampaignCreateResponse(BaseModel):
    thread_id: str
    status: str

from src.models.campaign_state import ReviewStatus


class HITLDecision(BaseModel):
    review_status: ReviewStatus
    approved_variant_id: str = ""
    human_modifications: dict[str, Any] = Field(default_factory=dict)

class APIResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None
