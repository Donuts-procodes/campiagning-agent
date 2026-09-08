from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AccountStatus(str, Enum):
    PROSPECT = "prospect"
    ENGAGED = "engaged"
    CUSTOMER = "customer"
    ARCHIVED = "archived"

class ContactStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    ENROLLED = "enrolled"
    SEQUENCE_ACTIVE = "sequence_active"
    REPLIED = "replied"
    MEETING_BOOKED = "meeting_booked"
    CONVERTED = "converted"
    ARCHIVED = "archived"

class Account(BaseModel):
    account_id: str
    company_name: str
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    status: AccountStatus = AccountStatus.PROSPECT
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class Contact(BaseModel):
    contact_id: str
    account_id: str | None = None
    name: str
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    status: ContactStatus = ContactStatus.NEW
    
    # Attribution & Pipeline tracking (jj.mmd Downstream CRM)
    attribution_source: str = "direct" # meta_ads, google_ads, web_form, demo_request, csv_upload, ai_sourcing
    ad_id: str | None = None
    form_id: str | None = None
    utm_tags: dict[str, str] = Field(default_factory=dict)
    deal_value: float = 0.0
    
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class Enrollment(BaseModel):
    enrollment_id: str
    contact_id: str
    campaign_thread_id: str
    variant_id: str
    enrolled_at: datetime
    status: str = "active" # active, paused, finished
    attribution_source: str = "direct"
    utm_tags: dict[str, str] = Field(default_factory=dict)

class OutreachTask(BaseModel):
    task_id: str
    contact_id: str
    enrollment_id: str | None = None
    action_type: str # connect, message, email, call
    channel: str
    due_date: datetime
    status: str = "pending" # pending, completed, skipped
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
