"""Models for the application."""

from pydantic import BaseModel, Field


class Payload(BaseModel):
    """Payload model for incoming requests."""

    email: str
    secret: str
    task: str
    round_: int = Field(..., alias="round")
    nonce: str
    brief: str
    checks: list[str]
    evaluation_url: str
    attachments: list[dict]
