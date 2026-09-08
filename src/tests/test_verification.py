import pytest

from src.agents.verification_pod import compliance_checker
from src.models.campaign_state import CampaignState, VerificationState


@pytest.mark.asyncio
async def test_compliance_checker(sample_campaign_state: CampaignState):
    # This is a very basic test since compliance_checker just uses a dummy implementation right now
    result = await compliance_checker(sample_campaign_state)
    assert "verification" in result
    
    verification: VerificationState = result["verification"]
    assert verification.all_passed is True
    assert len(verification.audit_errors) == 0
