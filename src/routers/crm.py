from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.models.campaign import APIResponse
from src.services.crm_service import CRMService

router = APIRouter(tags=["crm"], prefix="/crm")

class AccountCreate(BaseModel):
    company_name: str
    domain: str | None = None
    industry: str | None = None

class ContactCreate(BaseModel):
    name: str
    account_id: str | None = None
    email: str | None = None

@router.post("/accounts", response_model=APIResponse)
async def create_account(payload: AccountCreate) -> APIResponse:
    data = await CRMService.create_account(**payload.model_dump())
    return APIResponse(success=True, data=data)

@router.get("/accounts", response_model=APIResponse)
async def list_accounts() -> APIResponse:
    data = await CRMService.list_accounts()
    return APIResponse(success=True, data=data)

@router.post("/contacts", response_model=APIResponse)
async def create_contact(payload: ContactCreate) -> APIResponse:
    data = await CRMService.create_contact(**payload.model_dump())
    return APIResponse(success=True, data=data)

@router.get("/contacts", response_model=APIResponse)
async def list_contacts() -> APIResponse:
    data = await CRMService.list_contacts()
    return APIResponse(success=True, data=data)
