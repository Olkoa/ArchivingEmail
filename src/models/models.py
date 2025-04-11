from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class EmailAddress(BaseModel):
    email: str

    @field_validator('email')
    @classmethod
    def clean_email(cls, v):
        # First remove quotes around the whole address
        cleaned = v.strip().strip('"\'')

        # Only remove specific trailing characters that shouldn't be part of an email
        if cleaned and cleaned[-1] in ";,":
            cleaned = cleaned[:-1]

        # Validate it has basic email format
        if '@' not in cleaned or '.' not in cleaned.split('@')[1]:
            raise ValueError(f"Invalid email format: {cleaned}")
        return cleaned

class MailingList(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    email_address: EmailAddress

class Organisation(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    email_address: EmailAddress

class Position(BaseModel):
    id: str
    name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    organisation: Organisation

class Entity(BaseModel):
    name: str
    alias_names: Optional[List[str]] = None
    is_physical_person: bool = True
    email: EmailAddress
    alias_emails: Optional[List[EmailAddress]] = None
    positions: Optional[List[Position]] = None

class Attachment(BaseModel):
    filename: str
    content: bytes
    content_type: Optional[str] = None
    size: Optional[int] = None

class ReceiverEmail(BaseModel):
    id: str
    sender_email: SenderEmail
    sender: Optional[Entity] = None
    to: Optional[List[Entity]] = None
    reply_to: Optional[Entity] = None
    cc: Optional[List[Entity]] = None
    bcc: Optional[List[Entity]] = None
    timestamp: datetime
    subject: str
    body: str
    attachments: Optional[List[Attachment]] = None
    is_deleted: bool = False
    folder: str = "inbox"
    is_spam: bool = False
    mailing_list: Optional[MailingList] = None
    importance_score: int = Field(default=0, ge=0, le=10)
    mother_email: Optional[ReceiverEmail] = None
    children_emails: Optional[List[ReceiverEmail]] = None

class SenderEmail(BaseModel):
    id: str
    sender: Entity
    body: str
    timestamp: datetime
    receiver_emails: Optional[List[ReceiverEmail]] = None
