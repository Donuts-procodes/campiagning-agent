import pytest
from datetime import date

from src.models.campaign_state import (
    CampaignState,
    CampaignType,
    CreativeBundle,
    CreativeBundleState,
    EmailSequence,
    UserInputState,
)
from src.agents.verification_pod import compliance_checker
from src.services.rag_service import chunk_content, clean_content


def test_clean_content_removes_noise():
    raw_html = """
    <html>
        <head><style>body { color: red; }</style></head>
        <body>
            <script>alert("test");</script>
            <h1>Product Overview</h1>
            <p>Our SaaS tool decreases latency by 50%.</p>
        </body>
    </html>
    """
    cleaned = clean_content(raw_html)
    assert "<script>" not in cleaned
    assert "<style>" not in cleaned
    assert "Product Overview" in cleaned
    assert "Our SaaS tool decreases latency by 50%." in cleaned


def test_deterministic_chunking():
    text = (
        "First paragraph detailing product features and architecture. " * 10
        + "\n\n"
        + "Second paragraph with customer proof points and metrics. " * 10
    )
    chunks = chunk_content(text, chunk_size=200, overlap=30)
    assert len(chunks) >= 2
    assert all(len(c) <= 250 for c in chunks)
    # Verify deterministic repeatability
    chunks_second_run = chunk_content(text, chunk_size=200, overlap=30)
    assert chunks == chunks_second_run


def test_user_input_state_defaults_and_fields():
    state = UserInputState(
        campaign_name="Test RAG Campaign",
        company_name="Acme Inc",
        product_service="Acme AI",
        value_proposition="Reduces ticket resolution time",
        target_icp="Support Directors",
        campaign_type=CampaignType.COLD_EMAIL,
        duration_days=30,
        start_date=date(2026, 10, 1),
        case_studies=["Client X reduced tickets by 35%"],
        differentiators=["100% On-Premise", "HIPAA Certified"],
        negative_constraints=["no pricing", "never say revolutionize"],
        brand_tone="challenger",
        primary_cta="soft_interest",
        sender_profile={"name": "Alex", "title": "Founder"},
    )
    assert state.brand_tone == "challenger"
    assert "no pricing" in state.negative_constraints
    assert len(state.case_studies) == 1
    assert state.sender_profile["title"] == "Founder"


@pytest.mark.asyncio
async def test_compliance_checker_enforces_negative_constraints():
    user_input = UserInputState(
        campaign_name="Guardrail Test",
        company_name="Acme",
        product_service="Security Tool",
        value_proposition="Protects cloud apps",
        target_icp="CISOs",
        campaign_type=CampaignType.COLD_EMAIL,
        duration_days=14,
        start_date=date(2026, 10, 1),
        negative_constraints=["revolutionize", "free audit"],
    )

    # Creative with forbidden term 'revolutionize'
    bundle = CreativeBundle(
        variant_id="variant_1",
        email_sequences=[
            EmailSequence(
                step_number=1,
                subject_line="Quick inquiry on cloud security",
                body_html="We can revolutionize your security operations. Interested?",
                variables_needed=[],
            )
        ],
    )

    state: CampaignState = {
        "user_input": user_input,
        "creatives": CreativeBundleState(variant_creatives={"variant_1": bundle}),
    }

    result = await compliance_checker(state)
    verification = result.get("verification")
    assert verification is not None
    assert verification.all_passed is False
    assert any(err.check_name == "negative_constraint" for err in verification.audit_errors)
