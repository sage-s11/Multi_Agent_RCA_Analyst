from pydantic import BaseModel, Field
from typing import Literal


class Ticket(BaseModel):
    ticket_id: str
    title: str
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    hostname: str
    interface: str
    created_at: str


class Device(BaseModel):
    hostname: str
    vendor: str
    model: str
    role: str
    site_code: str
    mgmt_ip: str


class SiteContact(BaseModel):
    site_code: str
    site_name: str
    contact_name: str
    contact_email: str
    contact_phone: str
    escalation_email: str


class TriageReport(BaseModel):
    ticket_id: str
    hostname: str
    interface: str
    site_code: str
    diagnosis_category: Literal["physical_layer", "admin_down", "err_disabled", "unknown"]
    likely_cause: str
    remote_steps: list[str] = Field(min_length=1)
    onsite_steps: list[str] = Field(min_length=1)
    site_contact_name: str
    site_contact_email: str
    draft_email_subject: str
    draft_email_body: str

class TriageJudgement(BaseModel):
    diagnosis_category: Literal["physical_layer", "admin_down", "err_disabled", "unknown"]
    likely_cause: str
    remote_steps: list[str] = Field(min_length=1)   # NOC does these via CLI
    onsite_steps: list[str] = Field(min_length=1)   # site contact does these
