"""FastAPI server for speech-to-text transcription."""

import yaml
import traceback
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pathlib import Path
from .transcriber import Transcriber
from .models import TranscriptionResponse, HealthResponse

# Load configuration
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize FastAPI app
app = FastAPI(
    title="Claude Voice STT Server",
    description="Speech-to-text server using Whisper with CUDA acceleration",
    version="1.0.0"
)

# Global transcriber instance
transcriber = None


@app.on_event("startup")
async def startup_event():
    """Initialize the transcriber on startup."""
    global transcriber
    transcriber = Transcriber()
    print(f"Server listening on {config['host']}:{config['port']}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns:
        Server status and model information
    """
    return HealthResponse(
        status="healthy",
        model=config['model']['name'],
        device=config['model']['device']
    )


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(..., description="WAV audio file (16kHz, mono, PCM16)"),
    language: str = Form(None, description="Language code (e.g., 'en'), or auto-detect if omitted")
):
    """Transcribe audio to text.

    Args:
        audio: Uploaded WAV audio file
        language: Optional language code

    Returns:
        Transcription result with text and metadata

    Raises:
        HTTPException: If transcription fails
    """
    if transcriber is None:
        raise HTTPException(status_code=503, detail="Transcriber not initialized")

    try:
        audio_bytes = await audio.read()
        print(f"Received audio: {len(audio_bytes)} bytes")
        result = transcriber.transcribe(audio_bytes, language)
        return TranscriptionResponse(**result)
    except Exception as e:
        print(f"Error during transcription: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Claude Voice STT Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "transcribe": "/transcribe"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=config['host'],
        port=config['port'],
        reload=False
    )
