from typing import Optional

from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    session_id: str
    message: str
    system_prompt: Optional[str] = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str):
        value = value.strip()

        if not value or len(value) > 128:
            raise ValueError(
                "session_id must be between 1 and 128 characters"
            )

        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str):
        value = value.strip()

        if not value or len(value) > 4000:
            raise ValueError(
                "message must be between 1 and 4000 characters"
            )

        return value

class ChatMetadata(BaseModel):
    resolution_source: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    key_id: Optional[str] = None
    fallback_attempts: int


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: ChatMetadata