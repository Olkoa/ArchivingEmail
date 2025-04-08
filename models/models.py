from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from __future__ import annotations

class EmailAddress(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$') # must be a valid email address

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

class ReceiverEmail(BaseModel):
    id: str
    sender_email: SenderEmail
    sender: Entity
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