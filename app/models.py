"""Models for the application."""

from typing import Optional
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Attachmennt model for incoming requests."""

    name: str
    data: str = Field(..., alias="url")


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
    attachments: list[Attachment]


class LLMResponse(BaseModel):
    """Model for LLM response"""

    README: str = Field(..., alias="README.md", title="README.md")
    License: str = Field(..., alias="LICENSE", title="LICENSE")
    html_code: str = Field(..., alias="index.html", title="index.html")
    json_code: Optional[str] = Field(
        None, alias="script.js", title="script.js"
    )
    python_code: Optional[str] = Field(None, alias="main.py", title="main.py")
