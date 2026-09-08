from datetime import date

import pytest

from src.models.campaign_state import (
    AnalysisState,
    CadenceStep,
    CampaignState,
    CampaignType,
    CreativeBundleState,
    EnrichedICP,
    GroundingCitation,
    HITLState,
    ObjectiveOKR,
    OutreachVariant,
    ReviewStatus,
    StrategyState,
    UserInputState,
)


@pytest.fixture
def sample_user_input() -> UserInputState:
    return UserInputState(
        campaign_name="Q4 SaaS Leads",
        company_name="Acme Corp",
        product_service="AI Customer Support",
        value_proposition="Reduces ticket time by 40%",
        target_icp="VP of CS at mid-market tech",
        competitors=["Competitor A", "Competitor B"],
        campaign_type=CampaignType.MULTI_CHANNEL,
        target_meetings=15,
        duration_days=30,
        start_date=date(2026, 10, 1),
        business_okrs=[
            ObjectiveOKR(
                objective="Maximize Pipeline",
                key_results=["Generate 15 meetings", "Close 2 deals"],
            )
        ],
    )


@pytest.fixture
def sample_analysis() -> AnalysisState:
    return AnalysisState(
        sufficiency_score=0.9,
        is_sufficient=True,
        grounding_citations=[
            GroundingCitation(
                source_id="crm_001",
                content_snippet="Past campaigns for this persona had a 2% reply rate.",
                similarity_score=0.88,
            )
        ],
        enriched_icps=[
            EnrichedICP(
                segment_name="Mid-Market VP CS",
                firmographics="B2B SaaS, 100-500 employees",
                target_titles=["VP Customer Success", "Head of CS"],
                pain_points=["High support volume", "Agent churn"],
                estimated_tam=5000,
            )
        ]
    )


@pytest.fixture
def sample_strategy() -> StrategyState:
    return StrategyState(
        target_meetings=15,
        estimated_reply_rate=0.02,
        required_contact_volume=750,
        strategy_variants=[
            OutreachVariant(
                variant_id="v1",
                variant_name="Value First",
                description="Focus on the 40% time reduction",
                messaging_angle="ROI and efficiency",
                estimated_reply_rate=0.025,
                required_contact_volume=600,
                selected_channels=["email", "linkedin"],
                cadence_timeline=[
                    CadenceStep(day=1, channel="linkedin", action_type="connect"),
                    CadenceStep(day=2, channel="email", action_type="message")
                ]
            )
        ],
    )


@pytest.fixture
def sample_campaign_state(sample_user_input, sample_analysis, sample_strategy) -> CampaignState:
    return CampaignState(
        user_input=sample_user_input,
        analysis=sample_analysis,
        strategy=sample_strategy,
        creatives=CreativeBundleState(),
        hitl=HITLState(review_status=ReviewStatus.PENDING),
        revision_count=0,
        current_node=None,
        error=None,
    )
