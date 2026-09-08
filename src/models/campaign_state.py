from __future__ import annotations

import operator
from datetime import date, datetime, timezone
from enum import Enum
from typing import Annotated, Any
from typing_extensions import TypedDict

from pydantic import BaseModel, Field


class CampaignType(str, Enum):
    COLD_EMAIL = "cold_email"
    LINKEDIN_OUTREACH = "linkedin_outreach"
    ABM = "abm"
    PRODUCT_LAUNCH_PR = "product_launch_pr"
    PARTNER_AFFILIATE = "partner_affiliate"
    CONTENT_PROMOTION = "content_promotion"
    RETENTION_UPSELL = "retention_upsell"
    MULTI_CHANNEL = "multi_channel"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ObjectiveOKR(BaseModel):
    objective: str
    key_results: list[str]


class UserInputState(BaseModel):
    campaign_name: str
    company_name: str
    product_service: str
    value_proposition: str
    target_icp: str
    campaign_type: CampaignType = CampaignType.MULTI_CHANNEL
    duration_days: int = Field(gt=0)
    start_date: date
    business_okrs: list[ObjectiveOKR] = Field(default_factory=list)
    budget: float | None = None
    
    # Financial targets & allocation (ROAS & CAC)
    target_roas: float = 3.0
    target_cac: float | None = None
    budget_allocation: dict[str, float] = Field(default_factory=dict)
    
    # Extended context fields
    target_accounts: list[str] = Field(default_factory=list)
    target_personas: list[str] = Field(default_factory=list)
    content_assets: list[str] = Field(default_factory=list)
    launch_url: str | None = None
    partner_profile: str | None = None
    customer_segment: str | None = None
    trigger_event: str | None = None
    success_metrics: list[str] = Field(default_factory=list)
    channels_allowed: list[str] = Field(default_factory=list)
    credentials: dict[str, str] = Field(default_factory=dict)

    # High-precision AI steering & RAG grounding
    case_studies: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)
    past_winning_copy: list[str] = Field(default_factory=list)
    brand_tone: str = "direct_consultative"
    negative_constraints: list[str] = Field(default_factory=list)
    primary_cta: str = "soft_interest"
    sender_profile: dict[str, str] = Field(default_factory=dict)
    target_geography: str = "North America"
    pricing_tier: str = "mid_market"

    # Target prospect sourcing mode & initial contacts
    prospect_sourcing_mode: str = "ai_sourcing"  # "csv_upload" | "ai_sourcing"
    initial_contacts: list[dict[str, Any]] = Field(default_factory=list)

    # Legacy fields
    target_meetings: int = Field(default=10, gt=0)
    competitors: list[str] = Field(default_factory=list)


class GroundingCitation(BaseModel):
    source_id: str
    content_snippet: str
    similarity_score: float


class EnrichedICP(BaseModel):
    segment_name: str
    firmographics: str
    target_titles: list[str]
    pain_points: list[str]
    estimated_tam: int = 0


class AnalysisState(BaseModel):
    sufficiency_score: float = 0.0
    is_sufficient: bool = False
    grounding_citations: list[GroundingCitation] = Field(default_factory=list)
    enriched_icps: list[EnrichedICP] = Field(default_factory=list)


class CadenceStep(BaseModel):
    day: int
    channel: str  # email, linkedin, call
    action_type: str  # connect, message, follow_up


class OutreachVariant(BaseModel):
    variant_id: str
    variant_name: str
    description: str
    messaging_angle: str
    estimated_reply_rate: float = 0.0
    required_contact_volume: int = 0
    selected_channels: list[str] = Field(default_factory=list)
    cadence_timeline: list[CadenceStep] = Field(default_factory=list)
    target_segments: list[str] = Field(default_factory=list)
    assets_required: list[str] = Field(default_factory=list)
    execution_readiness: str = "draft"
    kpi_assumptions: dict[str, Any] = Field(default_factory=dict)
    target_roas: float = 3.0
    target_cac: float = 250.0
    channel_budgets: dict[str, float] = Field(default_factory=dict)


class StrategyState(BaseModel):
    target_meetings: int = 0
    estimated_reply_rate: float = 0.0
    required_contact_volume: int = 0
    target_roas: float = 3.0
    target_cac: float = 250.0
    budget_allocation: dict[str, float] = Field(default_factory=dict)
    historical_roas_cac_feedback: dict[str, Any] = Field(default_factory=dict)
    strategy_variants: list[OutreachVariant] = Field(default_factory=list)


class EmailSequence(BaseModel):
    step_number: int
    subject_line: str
    body_html: str
    variables_needed: list[str] = Field(default_factory=list)


class LinkedInScript(BaseModel):
    step_number: int
    message_type: str # connection_request, follow_up
    text: str


class CallScript(BaseModel):
    step_number: int
    script_text: str


class GenericAsset(BaseModel):
    asset_type: str
    content_text: str
    variables_needed: list[str] = Field(default_factory=list)


class AdCreative(BaseModel):
    ad_id: str = ""
    platform: str = "meta"  # meta, google, inbound_landing
    headline: str
    body_copy: str
    call_to_action: str
    target_placement: str = "feed"
    utm_parameters: dict[str, str] = Field(default_factory=dict)


class InboundFormSpec(BaseModel):
    form_id: str = ""
    form_name: str
    landing_url: str = ""
    headline: str
    description: str
    fields_required: list[str] = Field(default_factory=lambda: ["name", "email", "company_name"])
    webhook_endpoint: str = ""


class CreativeBundle(BaseModel):
    variant_id: str
    email_sequences: list[EmailSequence] = Field(default_factory=list)
    linkedin_scripts: list[LinkedInScript] = Field(default_factory=list)
    call_scripts: list[CallScript] = Field(default_factory=list)
    generic_assets: list[GenericAsset] = Field(default_factory=list)
    ad_creatives: list[AdCreative] = Field(default_factory=list)
    inbound_forms: list[InboundFormSpec] = Field(default_factory=list)


class CreativeBundleState(BaseModel):
    variant_creatives: dict[str, CreativeBundle] = Field(default_factory=dict)


class AuditError(BaseModel):
    check_name: str
    message: str
    severity: str = "error"


class VerificationState(BaseModel):
    spam_words_check: bool = False
    variables_check: bool = False
    compliance_check_passed: bool = False
    all_passed: bool = False
    audit_errors: list[AuditError] = Field(default_factory=list)


class HITLState(BaseModel):
    approved_variant_id: str = ""
    human_modifications: dict[str, Any] = Field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.PENDING


class ExecutionReceipt(BaseModel):
    channel: str
    job_id: str = ""
    contacts_enrolled: int = 0
    status: str = "pending"
    response_payload: dict[str, Any] = Field(default_factory=dict)
    dispatched_at: datetime | None = None


class ExecutionReceiptState(BaseModel):
    receipts: list[ExecutionReceipt] = Field(default_factory=list)


def _replace(existing: Any, new: Any) -> Any:
    if new is not None:
        return new
    return existing


def _merge_creatives(
    existing: CreativeBundleState | None,
    new: CreativeBundleState | None,
) -> CreativeBundleState | None:
    if not existing and not new:
        return None
    if not existing:
        return new
    if not new:
        return existing

    merged = dict(existing.variant_creatives)
    for variant_id, new_bundle in new.variant_creatives.items():
        if variant_id not in merged:
            merged[variant_id] = new_bundle
        else:
            eb = merged[variant_id]
            merged[variant_id] = CreativeBundle(
                variant_id=variant_id,
                email_sequences=new_bundle.email_sequences or eb.email_sequences,
                linkedin_scripts=new_bundle.linkedin_scripts or eb.linkedin_scripts,
                call_scripts=new_bundle.call_scripts or eb.call_scripts,
                generic_assets=new_bundle.generic_assets or eb.generic_assets,
                ad_creatives=new_bundle.ad_creatives or eb.ad_creatives,
                inbound_forms=new_bundle.inbound_forms or eb.inbound_forms,
            )
    return CreativeBundleState(variant_creatives=merged)


class ClosedLoopMetrics(BaseModel):
    total_spend: float = 0.0
    total_enrolled: int = 0
    active_sequences: int = 0
    replied_count: int = 0
    converted_count: int = 0
    actual_cac: float = 0.0
    target_cac: float = 0.0
    conversion_rate: float = 0.0
    actual_roas: float = 0.0
    target_roas: float = 0.0
    performance_status: str = "on_track"  # exceeding, on_track, underperforming
    channel_performance: dict[str, dict[str, Any]] = Field(default_factory=dict)
    optimization_recommendations: list[str] = Field(default_factory=list)
    budget_reallocations: dict[str, float] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClosedLoopState(BaseModel):
    latest_evaluation: ClosedLoopMetrics | None = None
    evaluation_history: list[ClosedLoopMetrics] = Field(default_factory=list)


class CampaignState(TypedDict, total=False):
    user_input: Annotated[UserInputState | None, _replace]
    analysis: Annotated[AnalysisState | None, _replace]
    strategy: Annotated[StrategyState | None, _replace]
    creatives: Annotated[CreativeBundleState | None, _merge_creatives]
    verification: Annotated[VerificationState | None, _replace]
    hitl: Annotated[HITLState | None, _replace]
    execution: Annotated[ExecutionReceiptState | None, _replace]
    closed_loop: Annotated[ClosedLoopState | None, _replace]
    revision_count: Annotated[int, operator.add]
    current_node: Annotated[str | None, _replace]
    error: Annotated[str | None, _replace]
