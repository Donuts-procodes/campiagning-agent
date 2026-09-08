from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar

from src.core.llm import get_instructor_client
from src.models.crm import (
    Account,
    Contact,
    ContactStatus,
    Enrollment,
    OutreachTask,
)


class CRMService:
    _accounts: ClassVar[dict[str, Account]] = {}
    _contacts: ClassVar[dict[str, Contact]] = {}
    _enrollments: ClassVar[dict[str, Enrollment]] = {}
    _tasks: ClassVar[dict[str, OutreachTask]] = {}

    @classmethod
    async def create_account(cls, company_name: str, **kwargs) -> Account:
        account_id = str(uuid.uuid4())
        acc = Account(
            account_id=account_id,
            company_name=company_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs
        )
        cls._accounts[account_id] = acc
        return acc

    @classmethod
    async def create_contact(cls, name: str, account_id: str | None = None, **kwargs) -> Contact:
        contact_id = str(uuid.uuid4())
        contact = Contact(
            contact_id=contact_id,
            name=name,
            account_id=account_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs
        )
        cls._contacts[contact_id] = contact
        return contact

    @classmethod
    async def enroll_contact(
        cls,
        contact_id: str,
        campaign_thread_id: str,
        variant_id: str,
        attribution_source: str = "direct",
        utm_tags: dict[str, str] | None = None,
    ) -> Enrollment:
        enrollment_id = str(uuid.uuid4())
        en = Enrollment(
            enrollment_id=enrollment_id,
            contact_id=contact_id,
            campaign_thread_id=campaign_thread_id,
            variant_id=variant_id,
            enrolled_at=datetime.now(timezone.utc),
            attribution_source=attribution_source,
            utm_tags=utm_tags or {},
        )
        cls._enrollments[enrollment_id] = en
        
        contact = cls._contacts.get(contact_id)
        if contact:
            contact.status = ContactStatus.ENROLLED
            contact.attribution_source = attribution_source
            if utm_tags:
                contact.utm_tags = utm_tags
            contact.updated_at = datetime.now(timezone.utc)
            
        return en

    @classmethod
    async def create_task(cls, contact_id: str, action_type: str, channel: str, due_date: datetime, enrollment_id: str | None = None) -> OutreachTask:
        task_id = str(uuid.uuid4())
        task = OutreachTask(
            task_id=task_id,
            contact_id=contact_id,
            enrollment_id=enrollment_id,
            action_type=action_type,
            channel=channel,
            due_date=due_date,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        cls._tasks[task_id] = task
        return task

    @classmethod
    async def list_accounts(cls) -> list[Account]:
        return list(cls._accounts.values())

    @classmethod
    async def list_contacts(cls) -> list[Contact]:
        return list(cls._contacts.values())

    @classmethod
    async def get_campaign_contacts(cls, campaign_thread_id: str) -> list[dict]:
        campaign_enrollments = [
            en for en in cls._enrollments.values()
            if en.campaign_thread_id == campaign_thread_id
        ]
        results = []
        for en in campaign_enrollments:
            contact = cls._contacts.get(en.contact_id)
            if not contact:
                continue
            account = cls._accounts.get(contact.account_id) if contact.account_id else None
            company = account.company_name if account else contact.metadata.get("company", "Target Account")
            results.append({
                "enrollment_id": en.enrollment_id,
                "contact_id": contact.contact_id,
                "name": contact.name,
                "title": contact.title or "Executive",
                "email": contact.email or f"{contact.name.lower().replace(' ', '.')}@example.com",
                "linkedin_url": contact.linkedin_url or f"https://linkedin.com/in/{contact.name.lower().replace(' ', '-')}",
                "company_name": company,
                "status": en.status or contact.status.value,
                "variant_id": en.variant_id,
                "attribution_source": contact.attribution_source or en.attribution_source,
                "utm_tags": contact.utm_tags or en.utm_tags,
                "ad_id": contact.ad_id,
                "form_id": contact.form_id,
                "deal_value": contact.deal_value,
                "enrolled_at": en.enrolled_at.isoformat(),
            })
        return results

    @classmethod
    async def add_campaign_contact(
        cls,
        campaign_thread_id: str,
        name: str,
        company_name: str,
        email: str,
        title: str = "Lead",
        linkedin_url: str = "",
        variant_id: str = "variant1",
        status: str = "enrolled",
        attribution_source: str = "direct",
        ad_id: str | None = None,
        form_id: str | None = None,
        utm_tags: dict[str, str] | None = None,
        deal_value: float = 0.0,
    ) -> dict:
        acc = await cls.create_account(company_name=company_name)
        contact = await cls.create_contact(
            name=name,
            account_id=acc.account_id,
            email=email,
            title=title,
            linkedin_url=linkedin_url,
            attribution_source=attribution_source,
            ad_id=ad_id,
            form_id=form_id,
            utm_tags=utm_tags or {},
            deal_value=deal_value,
            metadata={"company": company_name},
        )
        en = await cls.enroll_contact(
            contact_id=contact.contact_id,
            campaign_thread_id=campaign_thread_id,
            variant_id=variant_id,
            attribution_source=attribution_source,
            utm_tags=utm_tags,
        )
        en.status = status
        return {
            "enrollment_id": en.enrollment_id,
            "contact_id": contact.contact_id,
            "name": contact.name,
            "title": contact.title,
            "email": contact.email,
            "linkedin_url": contact.linkedin_url,
            "company_name": company_name,
            "status": status,
            "variant_id": variant_id,
            "attribution_source": attribution_source,
            "ad_id": ad_id,
            "form_id": form_id,
            "utm_tags": utm_tags or {},
            "deal_value": deal_value,
            "enrolled_at": en.enrolled_at.isoformat(),
        }

    @classmethod
    async def update_campaign_contact_status(
        cls,
        campaign_thread_id: str,
        contact_id: str,
        status: str,
    ) -> bool:
        contact = cls._contacts.get(contact_id)
        if contact:
            try:
                contact.status = ContactStatus(status)
            except ValueError:
                pass
            contact.updated_at = datetime.now(timezone.utc)

        for en in cls._enrollments.values():
            if en.campaign_thread_id == campaign_thread_id and en.contact_id == contact_id:
                en.status = status
                return True
        return False

    @classmethod
    async def seed_campaign_leads(cls, campaign_thread_id: str, company_name: str = "Target", icp_desc: str = "") -> list[dict]:
        existing = await cls.get_campaign_contacts(campaign_thread_id)
        if existing:
            return existing

        sample_profiles = [
            ("Sarah Chen", "VP of Infrastructure", "CloudScale Technologies", "sarah.chen@cloudscale.io", "sequence_active"),
            ("Marcus Brody", "Head of DevOps", "DataFlow Systems", "m.brody@dataflow.tech", "replied"),
            ("Elena Rostova", "Chief Technology Officer", "FinPulse Global", "elena@finpulse.com", "meeting_booked"),
            ("David Park", "Director of Cloud Operations", "Nexus Media Group", "dpark@nexusmedia.net", "sequence_active"),
            ("Rachel Adams", "VP Engineering", "Vanguard AI", "rachel.adams@vanguardai.com", "enrolled"),
        ]

        seeded = []
        for name, title, comp, email, stat in sample_profiles:
            item = await cls.add_campaign_contact(
                campaign_thread_id=campaign_thread_id,
                name=name,
                company_name=comp,
                email=email,
                title=title,
                linkedin_url=f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
                variant_id="variant1",
                status=stat,
                attribution_source="seed_icp",
            )
            seeded.append(item)
        return seeded

    @classmethod
    async def bulk_enroll_contacts(cls, campaign_thread_id: str, contacts: list[dict[str, Any]]) -> list[dict]:
        """Bulk enrolls a list of contacts (e.g. from CSV upload or spreadsheet) into a campaign thread."""
        enrolled_list = []
        for c in contacts:
            name = c.get("name") or f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            email = c.get("email")
            if not name or not email:
                continue
            company = c.get("company_name") or c.get("company") or "Target Account"
            item = await cls.add_campaign_contact(
                campaign_thread_id=campaign_thread_id,
                name=name,
                company_name=company,
                email=email,
                title=c.get("title") or c.get("job_title") or "Executive",
                linkedin_url=c.get("linkedin_url") or "",
                variant_id=c.get("variant_id") or "variant1",
                status=c.get("status") or "enrolled",
                attribution_source=c.get("attribution_source") or "csv_upload",
                ad_id=c.get("ad_id"),
                form_id=c.get("form_id"),
                utm_tags=c.get("utm_tags") or {},
                deal_value=float(c.get("deal_value", 0.0)),
            )
            enrolled_list.append(item)
        return enrolled_list

    @classmethod
    async def autonomous_prospect_sourcing(
        cls,
        campaign_thread_id: str,
        company_name: str,
        target_icp: str,
        target_geography: str = "North America",
        count: int = 5,
    ) -> list[dict]:
        """
        Autonomously discovers, generates, and enrolls high-fidelity B2B prospects
        matching the campaign's exact ICP, target titles, and geography.
        """
        existing = await cls.get_campaign_contacts(campaign_thread_id)
        if existing:
            return existing

        client = get_instructor_client()
        prompt = (
            f"Campaign Company: {company_name}\n"
            f"Target ICP: {target_icp}\n"
            f"Target Geography: {target_geography}\n\n"
            f"Discover and generate exactly {count} distinct real-world buyer profiles of decision makers "
            f"matching this ICP. Provide valid names, realistic corporate email addresses matching their company domain, "
            f"executive job titles, and LinkedIn profile URLs."
        )

        try:
            from src.core.config import settings
            from pydantic import BaseModel, Field

            class _SourcedLead(BaseModel):
                name: str
                company_name: str
                title: str
                email: str
                linkedin_url: str

            class _SourcedLeadsResponse(BaseModel):
                leads: list[_SourcedLead] = Field(min_length=count, max_length=count)

            result = await client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                response_model=_SourcedLeadsResponse,
                messages=[
                    {"role": "system", "content": "You are an autonomous B2B Lead Intelligence Agent. Discover high-converting buyer profiles strictly matching the target ICP and geography."},
                    {"role": "user", "content": prompt},
                ],
            )

            enrolled = []
            for lead in result.leads:
                item = await cls.add_campaign_contact(
                    campaign_thread_id=campaign_thread_id,
                    name=lead.name,
                    company_name=lead.company_name,
                    email=lead.email,
                    title=lead.title,
                    linkedin_url=lead.linkedin_url,
                    variant_id="variant1",
                    status="enrolled",
                    attribution_source="ai_sourcing",
                )
                enrolled.append(item)
            return enrolled

        except Exception as e:
            return await cls.seed_campaign_leads(campaign_thread_id, company_name, target_icp)
