from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.llm import get_instructor_client
from src.models.campaign_state import (
    AdCreative,
    CallScript,
    CampaignState,
    CampaignType,
    CreativeBundle,
    CreativeBundleState,
    EmailSequence,
    GenericAsset,
    InboundFormSpec,
    LinkedInScript,
)

logger = logging.getLogger(__name__)

def sanitize_and_normalize_copy(text: str) -> tuple[str, list[str]]:
    """
    1. Replaces non-standard unicode/curly punctuation with standard ASCII 
       equivalents to eliminate CP1252 / terminal encoding artifacts.
    2. Enforces Jinja2 merge syntax: e.g. [FirstName], [First Name], {{First_Name}} -> {{first_name}}.
    3. Returns normalized text and list of extracted variables.
    """
    if not text:
        return text, []

    # 1. Unicode typographic replacements
    replacements = {
        "\u2018": "'",  # Left single curly quote
        "\u2019": "'",  # Right single curly quote (apostrophe)
        "\u201a": "'",  # Single low-9 quote
        "\u201b": "'",  # Single high-reversed-9 quote
        "\u201c": '"',  # Left double curly quote
        "\u201d": '"',  # Right double curly quote
        "\u201e": '"',  # Double low-9 quote
        "\u201f": '"',  # Double high-reversed-9 quote
        "\u2013": "-",  # En-dash
        "\u2014": "--", # Em-dash
        "\u00a0": " ",  # Non-breaking space
        "\u2026": "...",# Horizontal ellipsis
    }
    for orig, target in replacements.items():
        text = text.replace(orig, target)

    # 2. Normalize merge variable placeholders
    patterns = [
        # First name variants: [First Name], [FirstName], [first_name], [Recipient's Name], [Name], {{First_Name}}, {{FirstName}}
        (r"\[(?:First\s*Name|FirstName|first_name|Recipient(?:'s)?\s*Name|Name)\]", "{{first_name}}"),
        (r"\{\{\s*(?:First\s*Name|FirstName|First_Name|first\s*name|name)\s*\}\}", "{{first_name}}"),
        
        # Last name variants: [Last Name], [LastName], {{Last_Name}}
        (r"\[(?:Last\s*Name|LastName|last_name)\]", "{{last_name}}"),
        (r"\{\{\s*(?:Last\s*Name|LastName|Last_Name|last\s*name)\s*\}\}", "{{last_name}}"),
        
        # Company name variants: [Company Name], [CompanyName], [Company], {{Company_Name}}
        (r"\[(?:Company\s*Name|CompanyName|Company|company_name)\]", "{{company_name}}"),
        (r"\{\{\s*(?:Company\s*Name|CompanyName|Company_Name|company)\s*\}\}", "{{company_name}}"),
        
        # Job title variants: [Job Title], [JobTitle], [Title]
        (r"\[(?:Job\s*Title|JobTitle|Title|job_title)\]", "{{job_title}}"),
        (r"\{\{\s*(?:Job\s*Title|JobTitle|Job_Title|title)\s*\}\}", "{{job_title}}"),
    ]
    for pat, rep in patterns:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)

    extracted_vars = sorted(list(set(re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", text))))
    return text, extracted_vars

class _CoreAssetResponse(BaseModel):
    emails: list[EmailSequence] = Field(default_factory=list)
    generic_assets: list[GenericAsset] = Field(default_factory=list)

class _SupplementaryAssetResponse(BaseModel):
    linkedin_scripts: list[LinkedInScript] = Field(default_factory=list)
    call_scripts: list[CallScript] = Field(default_factory=list)


async def email_sequence_generator(state: CampaignState) -> dict:
    user_input = state["user_input"]
    strategy = state.get("strategy")
    creatives = state.get("creatives") or CreativeBundleState()
    client = get_instructor_client()

    if not strategy or not strategy.strategy_variants:
        return {"current_node": "email_sequence_generator", "error": "No variants found"}

    new_bundles = dict(creatives.variant_creatives)
    c_type = user_input.campaign_type

    sender_str = ""
    if user_input.sender_profile:
        name = user_input.sender_profile.get("name", "")
        title = user_input.sender_profile.get("title", "")
        if name or title:
            sender_str = f"Sender Identity: {name} ({title})\n"

    citations = []
    if state.get("analysis") and state["analysis"].grounding_citations:
        citations = state["analysis"].grounding_citations
    proof_str = "\n".join([f"- {c.content_snippet}" for c in citations])
    if user_input.case_studies:
        proof_str += "\n" + "\n".join([f"- Case Study: {cs}" for cs in user_input.case_studies])

    formatting_rules = (
        "\n\nSTRICT COPYWRITING RULES & GUARDRAILS:\n"
        "- Length: STRICT LIMIT 50 to 90 words per email body. Cut all fluff.\n"
        "- Zero Generic Openers: NEVER use 'Hope this finds you well', 'Hope you are having a great week', 'My name is X'. Start directly with problem or observation.\n"
        "- Banned Hype Clichés: NEVER use 'game-changer', 'revolutionize', 'cutting-edge', 'streamline', 'synergy', 'delighted to', 'unlock potential', 'seamlessly'.\n"
        "- Subject Lines: 2 to 4 words max. Sentence case or lowercase. Sound internal (e.g. 'cloud spend question', 'egress bills note').\n"
        "- Call to Action (CTA): Soft, interest-based (e.g. 'Worth a quick peek?', 'Open to exploring this?'). Never ask for 30 mins.\n"
        "- Punctuation: Maximum 1 exclamation mark across the sequence. Use ASCII straight quotes (') only.\n"
        "- Merge Syntax: Strict Jinja2: {{first_name}}, {{company_name}}, {{job_title}}. Never use square brackets.\n"
        "- Variables: Explicitly declare all used variables in variables_needed for each email."
    )

    system_prompt_email = (
        "You are an elite Enterprise B2B Outbound Copywriter specializing in cold email deliverability and conversion.\n"
        "You write like a peer executive having a brief 1-on-1 discussion, NOT a marketing brochure or aggressive sales rep.\n"
        "Follow all strict copywriting rules and negative constraints without exception."
    )

    for variant in strategy.strategy_variants:
        prompt = (
            f"Campaign Type: {c_type.value}\n"
            f"Company: {user_input.company_name}\n"
            f"Value Prop: {user_input.value_proposition}\n"
            f"Messaging Angle: {variant.messaging_angle}\n"
            f"Brand Tone: {user_input.brand_tone}\n"
            f"Target CTA: {user_input.primary_cta}\n"
            f"{sender_str}"
            f"Verified Proof Points & Case Studies:\n{proof_str or 'N/A'}\n"
            f"{formatting_rules}\n\n"
        )
        
        if c_type == CampaignType.PRODUCT_LAUNCH_PR:
            prompt += "Write a PR Pitch Email and a generic Press Release Summary."
        elif c_type == CampaignType.PARTNER_AFFILIATE:
            prompt += "Write an email sequence to recruit affiliates, and a generic Partner Value Prop One-Pager."
        elif c_type == CampaignType.RETENTION_UPSELL:
            prompt += "Write an upsell email sequence and a generic Case Study Request."
        else:
            prompt += (
                f"Write a multi-step cold email sequence (2-4 emails) in the specified brand tone ({user_input.brand_tone}). "
                f"Use the verified proof points where appropriate. End with the target CTA format ({user_input.primary_cta})."
            )

        try:
            result = await client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                response_model=_CoreAssetResponse,
                messages=[
                    {"role": "system", "content": system_prompt_email},
                    {"role": "user", "content": prompt},
                ],
            )
            
            # Sanitize and normalize all generated emails & assets
            for seq in result.emails:
                clean_sub, sub_vars = sanitize_and_normalize_copy(seq.subject_line)
                clean_body, body_vars = sanitize_and_normalize_copy(seq.body_html)
                seq.subject_line = clean_sub
                seq.body_html = clean_body
                all_vars = set(seq.variables_needed or []) | set(sub_vars) | set(body_vars)
                seq.variables_needed = sorted(list(all_vars))

            for asset in result.generic_assets:
                clean_text, asset_vars = sanitize_and_normalize_copy(asset.content_text)
                asset.content_text = clean_text
                all_vars = set(asset.variables_needed or []) | set(asset_vars)
                asset.variables_needed = sorted(list(all_vars))

            existing_bundle = new_bundles.get(variant.variant_id, CreativeBundle(variant_id=variant.variant_id))
            existing_bundle.email_sequences = result.emails
            if result.generic_assets:
                existing_bundle.generic_assets.extend(result.generic_assets)
            new_bundles[variant.variant_id] = existing_bundle

        except Exception as e:
            logger.error(f"Core Asset Generation failed for {variant.variant_id}: {e}")

    return {
        "creatives": CreativeBundleState(variant_creatives=new_bundles),
        "current_node": "email_sequence_generator"
    }


async def social_outreach_generator(state: CampaignState) -> dict:
    user_input = state["user_input"]
    strategy = state.get("strategy")
    creatives = state.get("creatives") or CreativeBundleState()
    client = get_instructor_client()

    if not strategy or not strategy.strategy_variants:
        return {"current_node": "social_outreach_generator"}

    new_bundles = dict(creatives.variant_creatives)

    system_prompt_social = (
        "You are an expert LinkedIn Social Selling Specialist and SDR Outbound Coach.\n\n"
        "STRICT SOCIAL & CALL GUARDRAILS:\n"
        "1. LinkedIn Connection Request: HARD LIMIT under 250 characters (including spaces). NEVER pitch a product in the connection note. Focus on peer relevance or a thoughtful domain observation.\n"
        "2. LinkedIn Follow-Up: Max 50-70 words. Casual, conversational, zero pushiness.\n"
        "3. SDR Phone Script: Concise 30-second elevator structure:\n"
        "   - Permission opener ('Did I catch you in the middle of something?')\n"
        "   - 1-sentence acute problem statement\n"
        "   - Soft permission question ('Open to taking a look at how we solved this for {{company_name}}?').\n"
        "4. Use ASCII straight quotes (') and Jinja2 merge variables {{first_name}}, {{company_name}}."
    )

    for variant in strategy.strategy_variants:
        prompt = (
            f"Company: {user_input.company_name}\n"
            f"Value Prop: {user_input.value_proposition}\n"
            f"Messaging Angle: {variant.messaging_angle}\n\n"
            f"Generate a 2-step LinkedIn outreach sequence (connection note under 250 characters + follow-up message) AND a short 30-second Call Script for SDRs.\n"
            f"Adhere strictly to character limits and Jinja2 variables like {{{{first_name}}}}."
        )

        try:
            result = await client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                response_model=_SupplementaryAssetResponse,
                messages=[
                    {"role": "system", "content": system_prompt_social},
                    {"role": "user", "content": prompt},
                ],
            )
            
            for script in result.linkedin_scripts:
                clean_text, _ = sanitize_and_normalize_copy(script.text)
                script.text = clean_text

            for call in result.call_scripts:
                clean_text, _ = sanitize_and_normalize_copy(call.script_text)
                call.script_text = clean_text

            existing_bundle = new_bundles.get(variant.variant_id, CreativeBundle(variant_id=variant.variant_id))
            existing_bundle.linkedin_scripts = result.linkedin_scripts
            existing_bundle.call_scripts = result.call_scripts
            new_bundles[variant.variant_id] = existing_bundle

        except Exception as e:
            logger.error(f"Supplementary Asset Generation failed for {variant.variant_id}: {e}")

    return {
        "creatives": CreativeBundleState(variant_creatives=new_bundles),
        "current_node": "social_outreach_generator"
    }


class _MediaAdResponse(BaseModel):
    ad_creatives: list[AdCreative] = Field(default_factory=list)
    inbound_forms: list[InboundFormSpec] = Field(default_factory=list)


async def media_ad_generator(state: CampaignState) -> dict:
    """
    Media Execution Generator (jj.mmd Stage 2):
    Generates Meta Ads, Google Ads, and Inbound Lead Capture Forms with tracking UTM parameters.
    """
    user_input = state["user_input"]
    strategy = state.get("strategy")
    creatives = state.get("creatives") or CreativeBundleState()
    client = get_instructor_client()

    if not strategy or not strategy.strategy_variants:
        return {"current_node": "media_ad_generator"}

    new_bundles = dict(creatives.variant_creatives)

    system_prompt_media = (
        "You are a Senior Performance Marketing and Paid Acquisition Director.\n"
        "Generate high-CTR B2B ad copy and inbound demo capture specifications.\n"
        "Include: 1 Meta feed ad, 1 Google Search ad, and 1 high-converting inbound landing form spec with clear UTM tracking."
    )

    for variant in strategy.strategy_variants:
        prompt = (
            f"Company: {user_input.company_name}\n"
            f"Product: {user_input.product_service}\n"
            f"Value Prop: {user_input.value_proposition}\n"
            f"Target ICP: {user_input.target_icp}\n"
            f"Messaging Angle: {variant.messaging_angle}\n\n"
            f"Create paid media ad units (Meta Ads, Google Ads) and an inbound lead generation form."
        )

        try:
            result = await client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                response_model=_MediaAdResponse,
                messages=[
                    {"role": "system", "content": system_prompt_media},
                    {"role": "user", "content": prompt},
                ],
            )
            existing_bundle = new_bundles.get(variant.variant_id, CreativeBundle(variant_id=variant.variant_id))
            existing_bundle.ad_creatives = result.ad_creatives
            existing_bundle.inbound_forms = result.inbound_forms
            new_bundles[variant.variant_id] = existing_bundle
        except Exception as e:
            logger.warning(f"Media ad generation fallback for {variant.variant_id}: {e}")
            # Reliable fallback adhering to schema
            fallback_ads = [
                AdCreative(
                    ad_id=f"meta_{variant.variant_id}",
                    platform="meta",
                    headline=f"Cut {user_input.company_name} Bottlenecks by 40%",
                    body_copy=f"{user_input.value_proposition}. Engineered specifically for {user_input.target_icp}.",
                    call_to_action="Book Priority Demo",
                    target_placement="feed",
                    utm_parameters={"utm_source": "meta", "utm_medium": "cpc", "utm_campaign": variant.variant_id},
                ),
                AdCreative(
                    ad_id=f"google_{variant.variant_id}",
                    platform="google",
                    headline=f"{user_input.company_name} | {user_input.product_service}",
                    body_copy=f"Evaluate {user_input.company_name}. Fast integration and measurable ROI.",
                    call_to_action="Get Started",
                    target_placement="search_top",
                    utm_parameters={"utm_source": "google", "utm_medium": "cpc", "utm_campaign": variant.variant_id},
                ),
            ]
            fallback_forms = [
                InboundFormSpec(
                    form_id=f"form_{variant.variant_id}",
                    form_name="B2B Evaluation Request",
                    landing_url=f"/demo/{user_input.company_name.lower().replace(' ', '-')}",
                    headline=f"Discover How {user_input.company_name} Delivers Value",
                    description=f"Fill out the brief form below to receive a personalized benchmark assessment.",
                    fields_required=["name", "email", "company_name", "title"],
                    webhook_endpoint="/api/campaigns/{thread_id}/inbound/webhook",
                )
            ]
            existing_bundle = new_bundles.get(variant.variant_id, CreativeBundle(variant_id=variant.variant_id))
            existing_bundle.ad_creatives = fallback_ads
            existing_bundle.inbound_forms = fallback_forms
            new_bundles[variant.variant_id] = existing_bundle

    return {
        "creatives": CreativeBundleState(variant_creatives=new_bundles),
        "current_node": "media_ad_generator"
    }
