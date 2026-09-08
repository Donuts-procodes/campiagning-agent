from __future__ import annotations

import logging

from src.models.campaign_state import (
    AuditError,
    CampaignState,
    CampaignType,
    VerificationState,
)

logger = logging.getLogger(__name__)

async def compliance_checker(state: CampaignState) -> dict:
    creatives = state.get("creatives")
    user_input = state.get("user_input")
    c_type = user_input.campaign_type if user_input else CampaignType.MULTI_CHANNEL
    errors = []
    
    spam_words_check = True
    variables_check = True
    asset_gap_check = True
    cta_check = True

    negative_constraints = user_input.negative_constraints if user_input and user_input.negative_constraints else []
    negative_constraint_check = True

    length_check = True
    cliche_check = True
    spam_triggers = ["guarantee", "risk-free", "100% free", "urgent", "act now", "congratulations", "winner"]
    banned_cliches = [
        "hope this email finds you well",
        "hope you are having a great",
        "game-changer",
        "revolutionize",
        "cutting-edge",
        "streamline your",
        "synergy",
        "delighted to",
    ]

    if creatives:
        for variant_id, bundle in creatives.variant_creatives.items():
            has_emails = len(bundle.email_sequences) > 0
            has_linkedin = len(bundle.linkedin_scripts) > 0
            has_generics = len(bundle.generic_assets) > 0

            # 1. Asset Gap Check
            if c_type == CampaignType.COLD_EMAIL and not has_emails:
                asset_gap_check = False
                errors.append(AuditError(check_name="asset_gap", message=f"{variant_id} missing cold emails"))
            if c_type == CampaignType.LINKEDIN_OUTREACH and not has_linkedin:
                asset_gap_check = False
                errors.append(AuditError(check_name="asset_gap", message=f"{variant_id} missing LinkedIn scripts"))
            if c_type in [CampaignType.PRODUCT_LAUNCH_PR, CampaignType.PARTNER_AFFILIATE, CampaignType.RETENTION_UPSELL]:
                if not has_generics:
                    asset_gap_check = False
                    errors.append(AuditError(check_name="asset_gap", message=f"{variant_id} missing generic campaign assets"))
            if c_type == CampaignType.MULTI_CHANNEL and not (has_emails and has_linkedin):
                asset_gap_check = False
                errors.append(AuditError(check_name="asset_gap", message=f"{variant_id} missing multi-channel coverage"))

            # 2. Email Specific Checks (Spam, CTA, Length, Variables, Negative Constraints, Cliches)
            for seq in bundle.email_sequences:
                sub = seq.subject_line.lower()
                body = seq.body_html.lower()

                # Spam Triggers
                for trigger in spam_triggers:
                    if trigger in sub:
                        spam_words_check = False
                        errors.append(AuditError(check_name="spam_words", message=f"Spam trigger '{trigger}' in subject of {variant_id} step {seq.step_number}"))

                # Cliché / Fluff Check
                for cliche in banned_cliches:
                    if cliche in body:
                        cliche_check = False
                        errors.append(AuditError(check_name="cliche_check", message=f"Banned cliché '{cliche}' in {variant_id} step {seq.step_number}"))

                # Word Count Check (Max 125 words)
                clean_words = body.replace("<br>", " ").replace("</p>", " ").split()
                if len(clean_words) > 130:
                    length_check = False
                    errors.append(AuditError(check_name="email_length", message=f"Email in {variant_id} step {seq.step_number} exceeds length limit ({len(clean_words)} words > 130 max)"))

                # Subject Line Length (Max 6 words)
                if len(sub.split()) > 6:
                    errors.append(AuditError(check_name="subject_length", message=f"Subject line in {variant_id} step {seq.step_number} too long ({len(sub.split())} words > 6 max)"))

                # Exclamation Mark Overuse
                if body.count("!") > 2:
                    errors.append(AuditError(check_name="exclamation_overuse", message=f"Too many exclamation marks in {variant_id} step {seq.step_number} ({body.count('!')} > 2)"))

                # Clear CTA Check
                if "?" not in body and "click here" not in body and "let me know" not in body and "reply" not in body:
                    cta_check = False
                    errors.append(AuditError(check_name="cta_check", message=f"Missing clear CTA in {variant_id} step {seq.step_number}"))

                # Variable Declaration Check
                if "{" in seq.body_html and "}" in seq.body_html:
                    if not seq.variables_needed:
                        variables_check = False
                        errors.append(AuditError(check_name="variables", message=f"Undeclared variables in {variant_id} step {seq.step_number}"))

                # Negative Constraints
                for constraint in negative_constraints:
                    c_clean = constraint.strip().lower()
                    if c_clean and (c_clean in sub or c_clean in body):
                        negative_constraint_check = False
                        errors.append(AuditError(
                            check_name="negative_constraint",
                            message=f"Violated forbidden constraint '{constraint}' in email {variant_id} step {seq.step_number}"
                        ))

            # 3. LinkedIn Checks (Character Limit & Constraints)
            for script in bundle.linkedin_scripts:
                script_text = script.text
                script_lower = script_text.lower()

                # Connection request hard limit: 280 characters
                if "connection" in script.message_type.lower() and len(script_text) > 280:
                    length_check = False
                    errors.append(AuditError(
                        check_name="linkedin_length",
                        message=f"LinkedIn connection request in {variant_id} exceeds 280 char limit ({len(script_text)} chars)"
                    ))

                for constraint in negative_constraints:
                    c_clean = constraint.strip().lower()
                    if c_clean and c_clean in script_lower:
                        negative_constraint_check = False
                        errors.append(AuditError(
                            check_name="negative_constraint",
                            message=f"Violated forbidden constraint '{constraint}' in LinkedIn {variant_id} step {script.step_number}"
                        ))

    all_passed = (
        spam_words_check
        and variables_check
        and asset_gap_check
        and cta_check
        and negative_constraint_check
        and length_check
        and cliche_check
    )
    
    return {
        "verification": VerificationState(
            spam_words_check=spam_words_check,
            variables_check=variables_check,
            compliance_check_passed=asset_gap_check and cta_check and length_check,
            all_passed=all_passed,
            audit_errors=errors
        ),
        "current_node": "compliance_checker",
        "revision_count": 1 if not all_passed else 0
    }
