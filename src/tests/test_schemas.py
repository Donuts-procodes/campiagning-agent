from datetime import date

import pytest

from src.models.campaign_state import (
    AnalysisState,
    AuditError,
    CadenceStep,
    CampaignType,
    CreativeBundle,
    EmailSequence,
    EnrichedICP,
    ExecutionReceipt,
    GroundingCitation,
    HITLState,
    ObjectiveOKR,
    OutreachVariant,
    ReviewStatus,
    StrategyState,
    UserInputState,
    VerificationState,
)


class TestUserInputState:
    def test_valid_creation(self):
        state = UserInputState(
            campaign_name="Custom Launch",
            company_name="Acme",
            product_service="Widget",
            value_proposition="Fast",
            target_icp="Everyone",
            campaign_type=CampaignType.COLD_EMAIL,
            target_meetings=10,
            duration_days=14,
            start_date=date(2026, 10, 1),
            business_okrs=[ObjectiveOKR(objective="Activate 50 partners", key_results=["Book 20 calls"])],
        )
        assert state.campaign_type == CampaignType.COLD_EMAIL
        assert state.target_meetings == 10

    def test_meetings_must_be_positive(self):
        with pytest.raises(Exception):
            UserInputState(
                campaign_name="X",
                company_name="X",
                product_service="X",
                value_proposition="X",
                target_icp="X",
                target_meetings=-5,
                duration_days=7,
                start_date=date(2026, 1, 1),
                business_okrs=[],
            )

    def test_duration_must_be_positive(self):
        with pytest.raises(Exception):
            UserInputState(
                campaign_name="X",
                company_name="X",
                product_service="X",
                value_proposition="X",
                target_icp="X",
                target_meetings=10,
                duration_days=0,
                start_date=date(2026, 1, 1),
                business_okrs=[],
            )


class TestAnalysisState:
    def test_defaults(self):
        state = AnalysisState()
        assert state.sufficiency_score == 0.0
        assert state.is_sufficient is False
        assert state.grounding_citations == []
        assert state.enriched_icps == []

    def test_round_trip_serialization(self):
        state = AnalysisState(
            sufficiency_score=0.9,
            is_sufficient=True,
            grounding_citations=[GroundingCitation(source_id="s1", content_snippet="test", similarity_score=0.9)],
            enriched_icps=[EnrichedICP(segment_name="Seg1", firmographics="firm", target_titles=["CEO"], pain_points=["Pain"], estimated_tam=1000)]
        )
        restored = AnalysisState.model_validate(state.model_dump(mode="json"))
        assert restored.sufficiency_score == 0.9
        assert restored.enriched_icps[0].segment_name == "Seg1"


class TestStrategyState:
    def test_variant_serialization(self):
        variant = OutreachVariant(
            variant_id="v1",
            variant_name="Test",
            description="A test variant",
            messaging_angle="Angle",
            estimated_reply_rate=0.02,
            required_contact_volume=500,
            selected_channels=["email"],
            cadence_timeline=[CadenceStep(day=1, channel="email", action_type="send")]
        )
        dumped = variant.model_dump(mode="json")
        assert dumped["variant_id"] == "v1"
        assert dumped["cadence_timeline"][0]["channel"] == "email"

    def test_strategy_state_defaults(self):
        state = StrategyState()
        assert state.target_meetings == 0
        assert state.strategy_variants == []


class TestCreativeBundle:
    def test_bundle_creation(self):
        bundle = CreativeBundle(
            variant_id="v1",
            email_sequences=[EmailSequence(step_number=1, subject_line="Hi", body_html="Hello", variables_needed=[])],
        )
        assert len(bundle.email_sequences) == 1
        assert bundle.email_sequences[0].subject_line == "Hi"


class TestVerificationState:
    def test_all_passed(self):
        state = VerificationState(
            spam_words_check=True,
            variables_check=True,
            compliance_check_passed=True,
            all_passed=True,
        )
        assert state.all_passed is True

    def test_with_errors(self):
        state = VerificationState(
            spam_words_check=False,
            audit_errors=[AuditError(check_name="test", message="failed")],
        )
        assert state.all_passed is False
        assert len(state.audit_errors) == 1


class TestHITLState:
    def test_review_status_enum(self):
        state = HITLState(review_status=ReviewStatus.APPROVED, approved_variant_id="v1")
        dumped = state.model_dump(mode="json")
        assert dumped["review_status"] == "approved"


class TestExecutionReceipt:
    def test_receipt_serialization(self):
        receipt = ExecutionReceipt(
            channel="email",
            job_id="job_123",
            contacts_enrolled=500,
            status="dispatched",
            response_payload={"id": "123"},
        )
        dumped = receipt.model_dump(mode="json")
        assert dumped["channel"] == "email"
        assert dumped["job_id"] == "job_123"
