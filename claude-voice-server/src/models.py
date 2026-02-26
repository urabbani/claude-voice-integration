"""Pydantic models for API requests and responses."""

from pydantic import BaseModel
from typing import Optional


class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    language: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response model for transcription results."""
    text: str
    duration: float
    language: str
    processing_time: float


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model: str
    device: str
