# Gemini Model Integration Guide

This guide explains how to integrate the Claude Voice STT Server with Google's Gemini AI models for advanced voice-to-text and text-to-speech workflows.

## Overview

```
┌─────────────────┐         ┌──────────────────────┐         ┌──────────────────┐
│   Voice Client  │         │   STT Server         │         │  Gemini AI      │
├─────────────────┤         ├──────────────────────┤         ├──────────────────┤
│ • Audio input   │ ──────▶ │ • faster-whisper    │ ──────▶ │ • Gemini Pro    │
│ • Hotkey       │  HTTP    │ • Transcription      │  HTTP   │ • Text gen      │
│ • Clipboard     │         │ • Language detection │  Text   │ • Image gen     │
└─────────────────┘         └──────────────────────┘         │ • Audio gen     │
                                                              └──────────────────┘
```

## Prerequisites

- Google Cloud account
- Gemini API key
- Voice STT Server running
- Python 3.8+

## Quick Start

### 1. Get Gemini API Key

```bash
# From Google Cloud Console
gcloud auth application-default login
export GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Basic Integration

```python
# src/gemini_integration.py
import requests
import json
from typing import Optional, Dict, Any

class GeminiIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_text(self, prompt: str, model: str = "gemini-pro") -> str:
        """Generate text from prompt"""
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
```

### 3. Voice-to-Gemini Workflow

```python
# src/voice_to_gemini.py
import asyncio
from src.gemini_integration import GeminiIntegration
from src.audio_transcriber import STTClient

class VoiceToGemini:
    def __init__(self, gemini_api_key: str, stt_server_url: str):
        self.gemini = GeminiIntegration(gemini_api_key)
        self.stt_client = STTClient(stt_server_url)

    async def process_voice_command(self, audio_file: str) -> Dict[str, Any]:
        """Process voice input through Gemini"""
        # Step 1: Transcribe audio
        transcription = await self.stt_client.transcribe(audio_file)

        # Step 2: Process with Gemini
        response = await self.gemini.generate_text(
            f"You transcribed: '{transcription['text']}'. "
            "What should I do with this input? Provide specific instructions."
        )

        return {
            "transcription": transcription,
            "gemini_response": response
        }
```

## Advanced Gemini Features

### 1. Multi-Modal Integration

```python
# src/gemini_multimodal.py
import base64
from pathlib import Path

class GeminiMultiModal:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def process_voice_and_image(self, audio_file: str, image_file: str) -> str:
        """Process voice input with image context"""
        # Transcribe audio first
        transcription = await self._transcribe_audio(audio_file)

        # Encode image
        image_base64 = self._encode_image(image_file)

        # Combine modalities
        prompt = f"""
        Voice command: '{transcription['text']}'
        Context image provided

        Analyze the voice command with the image context and provide relevant response.
        """

        # Create multimodal request
        url = f"{self.base_url}/models/gemini-pro-vision:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }]
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
```

### 2. Streaming Responses

```python
# src/gemini_streaming.py
import requests

class GeminiStreaming:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def stream_response(self, prompt: str):
        """Stream Gemini response chunks"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:streamGenerateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.7
            }
        }

        # Note: Actual streaming requires proper handling of Server-Sent Events
        # This is a simplified example
        response = requests.post(url, json=payload, stream=True)

        for line in response.iter_lines():
            if line:
                # Parse SSE format
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "candidates" in data:
                        yield data["candidates"][0]["content"]["parts"][0]["text"]
```

### 3. Function Calling

```python
# src/gemini_functions.py
import json
from typing import Callable, Dict, Any

class GeminiFunctions:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.functions = {}

    def register_function(self, name: str, description: str, parameters: Dict[str, Any], func: Callable):
        """Register a function for Gemini to call"""
        self.functions[name] = {
            "function": func,
            "description": description,
            "parameters": parameters
        }

    async def process_with_functions(self, user_input: str) -> str:
        """Process user input with function calling capability"""
        # Define available functions
        functions_schema = {
            "functions": [
                {
                    "name": name,
                    "description": desc["description"],
                    "parameters": desc["parameters"]
                }
                for name, desc in self.functions.items()
            ]
        }

        # Initial prompt
        prompt = f"""
        User input: '{user_input}'

        Available functions: {functions_schema}

        If appropriate, call the function with proper parameters. Otherwise, respond normally.
        """

        response = await self._generate_response(prompt, functions_schema)

        # Handle function calls
        if "function_call" in response:
            function_name = response["function_call"]["name"]
            arguments = json.loads(response["function_call"]["arguments"])

            # Execute function
            result = await self.functions[function_name]["function"](**arguments)

            # Follow-up response
            follow_up = f"Function '{function_name}' executed. Result: {result}"

            final_response = await self._generate_response(
                f"{follow_up}\n\nOriginal request: '{user_input}'",
                functions_schema
            )

            return final_response

        return response

    async def _generate_response(self, prompt: str, functions_schema: Dict[str, Any]) -> str:
        """Generate response with function schema"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "tools": [functions_schema] if functions_schema else None,
            "generationConfig": {
                "maxOutputTokens": 1024
            }
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
```

## Gemini Configuration

### 1. Configuration File

```yaml
# gemini_config.yaml
gemini:
  api_key: "${GEMINI_API_KEY}"
  models:
    text:
      default: "gemini-pro"
      options: ["gemini-pro", "gemini-pro-1.5"]
    vision:
      default: "gemini-pro-vision"
      options: ["gemini-pro-vision", "gemini-pro-vision-1.5"]

  generation_config:
    temperature: 0.7
    top_p: 0.95
    top_k: 40
    max_output_tokens: 1024

  safety_settings:
    - category: "HARM_CATEGORY_HARASSMENT"
      threshold: "BLOCK_LOW_AND_ABOVE"
    - category: "HARM_CATEGORY_HATE_SPEECH"
      threshold: "BLOCK_LOW_AND_ABOVE"
    - category: "HARM_CATEGORY_SEXUALLY_EXPLICIT"
      threshold: "BLOCK_LOW_AND_ABOVE"
    - category: "HARM_CATEGORY_DANGEROUS_CONTENT"
      threshold: "BLOCK_LOW_AND_ABOVE"

  voice_interaction:
    automatic_punctuation: true
    profanity_filter: true
    sentiment_analysis: true
```

### 2. Environment Variables

```bash
# .env file
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024
```

## Complete Integration Example

```python
# src/gemini_voice_assistant.py
import asyncio
import json
from typing import Dict, Any
from src.gemini_integration import GeminiIntegration
from src.gemini_functions import GeminiFunctions
from src.audio_transcriber import STTClient

class GeminiVoiceAssistant:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gemini = GeminiIntegration(config["gemini"]["api_key"])
        self.functions = GeminiFunctions(config["gemini"]["api_key"])
        self.stt_client = STTClient(config["stt_server_url"])

        # Setup functions
        self._setup_functions()

    def _setup_functions(self):
        """Setup available functions"""
        self.functions.register_function(
            name="get_weather",
            description="Get weather information for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            },
            func=self._get_weather
        )

        self.functions.register_function(
            name="set_reminder",
            description="Set a reminder",
            parameters={
                "type": "object",
                "properties": {
                    "time": {
                        "type": "string",
                        "description": "Time in HH:MM format"
                    },
                    "message": {
                        "type": "string",
                        "description": "Reminder message"
                    }
                },
                "required": ["time", "message"]
            },
            func=self._set_reminder
        )

    async def process_voice_command(self, audio_file: str) -> Dict[str, Any]:
        """Complete voice command processing"""
        # Step 1: Transcribe audio
        transcription = await self.stt_client.transcribe(audio_file)

        # Step 2: Process with Gemini
        try:
            response = await self.functions.process_with_functions(
                transcription["text"]
            )

            # Step 3: Generate voice response if needed
            if self.config.get("voice_response", False):
                audio_response = await self._generate_speech(response)
                return {
                    "transcription": transcription,
                    "response": response,
                    "audio_response": audio_response
                }

            return {
                "transcription": transcription,
                "response": response
            }

        except Exception as e:
            error_response = f"Error processing command: {str(e)}"
            return {
                "transcription": transcription,
                "response": error_response,
                "error": str(e)
            }

    async def _get_weather(self, location: str) -> str:
        """Get weather information"""
        # Implement weather API call
        return f"Weather in {location}: Sunny, 72°F"

    async def _set_reminder(self, time: str, message: str) -> str:
        """Set a reminder"""
        # Implement reminder logic
        return f"Reminder set for {time}: {message}"

    async def _generate_speech(self, text: str) -> bytes:
        """Generate speech from text"""
        # Implement TTS using Gemini or other service
        pass
```

## Docker Integration

### 1. Dockerfile for Gemini Integration

```dockerfile
# Dockerfile.gemini
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY config/ ./config/

# Set environment variables
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "src/gemini_server.py"]
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  voice-stt:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=medium
    volumes:
      - ./models:/app/models

  gemini-service:
    build:
      context: .
      dockerfile: Dockerfile.gemini
    ports:
      - "8001:8001"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - voice-stt

  voice-assistant:
    build:
      context: .
      dockerfile: Dockerfile.assistant
    ports:
      - "8002:8002"
    environment:
      - STT_SERVER_URL=http://voice-stt:8000
      - GEMINI_URL=http://gemini-service:8001
    depends_on:
      - voice-stt
      - gemini-service
```

## Performance Optimization

### 1. Model Caching

```python
# src/gemini_cache.py
import hashlib
import json
from pathlib import Path
from typing import Optional

class GeminiCache:
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt and model"""
        content = f"{prompt}:{model}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        cache_key = self.get_cache_key(prompt, model)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file, "r") as f:
                return json.load(f)

        return None

    def set(self, prompt: str, model: str, response: Dict[str, Any]):
        """Cache response"""
        cache_key = self.get_cache_key(prompt, model)
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, "w") as f:
            json.dump(response, f)
```

### 2. Batch Processing

```python
# src/gemini_batch.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

class GeminiBatchProcessor:
    def __init__(self, api_key: str, max_workers: int = 4):
        self.api_key = api_key
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch(self, prompts: list) -> list:
        """Process multiple prompts in parallel"""
        loop = asyncio.get_event_loop()

        tasks = []
        for prompt in prompts:
            task = loop.run_in_executor(
                self.executor,
                self._generate_single_response,
                prompt
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def _generate_single_response(self, prompt: str) -> Dict[str, Any]:
        """Generate single response"""
        # Implementation similar to GeminiIntegration.generate_text
        pass
```

## Monitoring and Logging

### 1. Request Logging

```python
# src/gemini_logger.py
import logging
from datetime import datetime
from typing import Dict, Any

class GeminiLogger:
    def __init__(self, log_file: str = "gemini.log"):
        self.logger = logging.getLogger("gemini")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_request(self, prompt: str, response: Dict[str, Any], duration: float):
        """Log request and response"""
        self.logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response_length": len(response.get("text", "")),
            "duration_ms": duration * 1000,
            "tokens_used": response.get("usage", {}).get("total_tokens", 0)
        }))
```

### 2. Performance Metrics

```python
# src/gemini_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Create metrics
GEMINI_REQUEST_COUNT = Counter('gemini_requests_total', 'Total Gemini requests')
GEMINI_REQUEST_DURATION = Histogram('gemini_request_duration_seconds', 'Gemini request duration')
GEMINI_TOKENS_USED = Gauge('gemini_tokens_used', 'Tokens used in last request')

class GeminiMetrics:
    @staticmethod
    def track_request(func):
        """Decorator to track metrics"""
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Update metrics
                GEMINI_REQUEST_COUNT.inc()
                duration = time.time() - start_time
                GEMINI_REQUEST_DURATION.observe(duration)

                # Extract tokens from response if available
                if isinstance(result, dict) and "usage" in result:
                    GEMINI_TOKENS_USED.set(result["usage"].get("total_tokens", 0))

                return result

            except Exception as e:
                GEMINI_REQUEST_COUNT.inc()
                raise e

        return wrapper
```

## Security Best Practices

### 1. API Key Management

```python
# src/secure_config.py
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self, key_file: str = "key.key"):
        self.key_file = key_file
        self.cipher_suite = self._load_or_create_key()

    def _load_or_create_key(self):
        """Load or create encryption key"""
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

    def get_api_key(self) -> str:
        """Get API key from environment or decrypt from file"""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key and os.path.exists("encrypted_api_key.enc"):
            with open("encrypted_api_key.enc", "r") as f:
                api_key = self.decrypt(f.read())

        return api_key
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Test API key
   curl -X POST \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"contents": [{"parts": [{"text": "Hello"}]}]}'
   ```

2. **Rate Limiting**
   ```python
   # Implement exponential backoff
   import time

   async def rate_limited_request(prompt: str):
       max_retries = 3
       for attempt in range(max_retries):
           try:
               return await self.gemini.generate_text(prompt)
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               wait_time = 2 ** attempt
               time.sleep(wait_time)
   ```

3. **Model Loading Issues**
   ```bash
   # Check available models
   curl -X GET \
     "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_API_KEY}"
   ```

### Debug Mode

```python
# src/gemini_debug.py
import logging

class GeminiDebug:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("gemini_debug")

        if debug_mode:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)

    def log_request(self, prompt: str, response: Dict[str, Any]):
        if self.debug_mode:
            self.logger.debug(f"Request: {prompt}")
            self.logger.debug(f"Response: {response}")

    def log_error(self, error: Exception):
        if self.debug_mode:
            self.logger.error(f"Error: {str(error)}", exc_info=True)
```