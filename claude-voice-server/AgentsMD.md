# AI Agent Integration Guide

This guide explains how to integrate the Claude Voice STT Server with various AI agents and assistants.

## Supported AI Agents

| Agent | Voice Input | Voice Output | Integration Type | Status |
|-------|-------------|--------------|------------------|--------|
| Claude 3.5 | ✅ | ❌ | Direct API | Production |
| OpenAI GPT-4 | ✅ | ✅ | API + TTS | Alpha |
| Anthropic Claude 3 | ✅ | ❌ | Direct API | Production |
| Google Gemini | ✅ | ❌ | API | Production |
| Meta Llama | ❌ | ❌ | RAG only | Beta |
| Custom Agents | ✅ | ✅ | API adapter | Custom |

## Quick Integration Methods

### Method 1: Direct API Integration

```python
# Direct voice-to-agent integration
import requests
import json

def send_to_agent(audio_file, agent_type="claude"):
    # First transcribe audio
    with open(audio_file, "rb") as f:
        response = requests.post(
            "http://YOUR_SERVER_IP:8000/transcribe",
            files={"audio": f}
        )

    if response.status_code == 200:
        transcribed_text = response.json()["text"]

        # Send to agent
        if agent_type == "claude":
            return send_to_claude(transcribed_text)
        elif agent_type == "openai":
            return send_to_openai(transcribed_text)
        # ... other agents

def send_to_claude(text):
    # Claude API integration
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "your-claude-api-key",
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [{
            "role": "user",
            "content": text
        }]
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=data
    )

    return response.json()["content"][0]["text"]

def send_to_openai(text):
    # OpenAI API integration
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-openai-api-key"
    }

    data = {
        "model": "gpt-4",
        "messages": [{
            "role": "user",
            "content": text
        }],
        "max_tokens": 1024
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data
    )

    return response.json()["choices"][0]["message"]["content"]
```

### Method 2: Agent Adapter Pattern

```python
# src/agents/base_agent.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    async def process_text(self, text: str) -> str:
        pass

    @abstractmethod
    async def get_name(self) -> str:
        pass

# src/agents/claude_agent.py
import requests

class ClaudeAgent(BaseAgent):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def process_text(self, text: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": text
            }]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )

        return response.json()["content"][0]["text"]

    async def get_name(self) -> str:
        return "Claude 3.5 Sonnet"

# src/agents/gemini_agent.py
class GeminiAgent(BaseAgent):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def process_text(self, text: str) -> str:
        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "contents": [{
                "parts": [{
                    "text": text
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 1024,
            }
        }

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}",
            headers=headers,
            json=data
        )

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    async def get_name(self) -> str:
        return "Google Gemini Pro"

# src/agents/agent_manager.py
from typing import Dict, List
import asyncio

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    async def process_with_agent(self, agent_name: str, text: str) -> str:
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")

        agent = self.agents[agent_name]
        return await agent.process_text(text)

    def list_agents(self) -> List[str]:
        return list(self.agents.keys())
```

## Advanced Integrations

### 1. Multi-Agent System

```python
# src/multi_agent_system.py
import asyncio
from agents import AgentManager, ClaudeAgent, GeminiAgent

class MultiAgentSystem:
    def __init__(self):
        self.manager = AgentManager()
        self.setup_agents()

    def setup_agents(self):
        # Register multiple agents
        self.manager.register_agent(
            "claude",
            ClaudeAgent("your-claude-api-key")
        )
        self.manager.register_agent(
            "gemini",
            GeminiAgent("your-gemini-api-key")
        )

    async def parallel_query(self, text: str, agents: List[str]) -> Dict[str, str]:
        tasks = []
        for agent_name in agents:
            task = asyncio.create_task(
                self.manager.process_with_agent(agent_name, text)
            )
            tasks.append((agent_name, task))

        results = {}
        for agent_name, task in tasks:
            try:
                results[agent_name] = await task
            except Exception as e:
                results[agent_name] = f"Error: {str(e)}"

        return results

    async def sequential_chain(self, text: str) -> str:
        # Chain multiple agents
        result = text

        # Step 1: Summarize with Claude
        result = await self.manager.process_with_agent(
            "claude",
            f"Summarize this text: {text}"
        )

        # Step 2: Analyze with Gemini
        result = await self.manager.process_with_agent(
            "gemini",
            f"Analyze this summary: {result}"
        )

        return result
```

### 2. RAG Integration

```python
# src/rag_integration.py
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import requests

class RAGIntegration:
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        self.vectorstore = None
        self.embeddings = OpenAIEmbeddings()
        self.setup_rag(knowledge_base_path)

    def setup_rag(self, path: str):
        # Load documents
        with open(path, "r") as f:
            documents = f.read().split("\n\n")

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.create_documents(documents)

        # Create vector store
        self.vectorstore = FAISS.from_documents(texts, self.embeddings)

    async def process_with_rag(self, query: str, agent: BaseAgent) -> str:
        # Similarity search
        relevant_docs = self.vectorstore.similarity_search(query, k=3)

        # Augment prompt
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        augmented_query = f"""Context:
{context}

Question: {query}

Answer based on the context and your knowledge:"""

        # Process with agent
        return await agent.process_text(augmented_query)
```

### 3. Voice Response Integration

```python
# src/voice_response.py
import requests
from pydub import AudioSegment
from io import BytesIO

class VoiceResponse:
    def __init__(self, tts_api_url: str = "https://api.openai.com/v1/audio/speech"):
        self.tts_api_url = tts_api_url

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        headers = {
            "Authorization": "Bearer your-tts-api-key",
            "Content-Type": "application/json"
        }

        data = {
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "speed": 1.0
        }

        response = requests.post(self.tts_api_url, headers=headers, json=data)
        return response.content

    async def play_response(self, audio_bytes: bytes):
        # Convert to AudioSegment
        audio = AudioSegment.from_wav(BytesIO(audio_bytes))

        # Play audio (requires sounddevice or pygame)
        import sounddevice as sd
        sd.play(audio.raw_data, samplerate=audio.frame_rate)
        sd.wait()
```

## Configuration Examples

### Agents Configuration

```yaml
# agents_config.yaml
agents:
  claude:
    type: "claude"
    api_key: "${CLAUDE_API_KEY}"
    model: "claude-3-sonnet-20240229"
    max_tokens: 1024

  gemini:
    type: "gemini"
    api_key: "${GEMINI_API_KEY}"
    model: "gemini-pro"

  gpt4:
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
    voice: "alloy"

  custom:
    type: "http"
    endpoint: "https://your-custom-agent.com/api"
    auth_header: "Authorization"
    auth_token: "${CUSTOM_API_TOKEN}"

routing:
  default_agent: "claude"
  fallback_agent: "gemini"

rag:
  enabled: true
  knowledge_base_path: "./knowledge_base"
  chunk_size: 1000

voice_response:
  enabled: true
  default_voice: "alloy"
  autoplay: true
```

## Agent Usage Examples

### 1. Voice Assistant with Multiple Agents

```python
# src/voice_assistant.py
import asyncio
from src.agents.agent_manager import AgentManager
from src.voice_response import VoiceResponse

class VoiceAssistant:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.voice = VoiceResponse()
        self.setup_agents()

    def setup_agents(self):
        # Setup agents as shown above

    async def handle_voice_command(self, audio_file):
        # Transcribe
        # Process with selected agent
        # Generate voice response if needed
```

### 2. Interactive Agent Selection

```python
# src/interactive_agent.py
import asyncio

class InteractiveAgent:
    async def run(self):
        agent_manager = AgentManager()
        # Register agents...

        while True:
            print("\nAvailable agents:")
            for agent in agent_manager.list_agents():
                print(f"- {agent}")

            agent_choice = input("Select agent (or 'exit'): ")
            if agent_choice == "exit":
                break

            user_input = input("Enter your query: ")

            try:
                response = await agent_manager.process_with_agent(
                    agent_choice,
                    user_input
                )
                print(f"\n{agent_choice} says: {response}")
            except Exception as e:
                print(f"Error: {str(e)}")
```

## Performance Optimization

### Batch Processing

```python
async def batch_process_audio_files(audio_files: List[str], agent_name: str):
    # Parallel transcription and processing
    tasks = []

    for audio_file in audio_files:
        task = asyncio.create_task(
            process_single_file(audio_file, agent_name)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Caching Responses

```python
import json
import hashlib
from pathlib import Path

class AgentCache:
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, text: str, agent: str):
        content = f"{text}:{agent}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, agent: str):
        cache_key = self.get_cache_key(text, agent)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file, "r") as f:
                return json.load(f)

        return None

    def set(self, text: str, agent: str, result: dict):
        cache_key = self.get_cache_key(text, agent)
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, "w") as f:
            json.dump(result, f)
```

## Deployment Examples

### Docker Compose with Multiple Agents

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
      - DEVICE=cuda
    volumes:
      - ./models:/app/models
      - ./config.yaml:/app/config.yaml

  claude-agent:
    build: ./agents
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}

  gemini-agent:
    build: ./agents
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}

  voice-assistant:
    build: ./assistant
    depends_on:
      - voice-stt
      - claude-agent
      - gemini-agent
    volumes:
      - ./config.yaml:/app/config.yaml
```

## Security Considerations

1. API Key Storage
   ```bash
   # Use environment variables
   export CLAUDE_API_KEY="your-api-key"

   # Or use Docker secrets
   echo "your-api-key" | docker secret create claude_api_key -
   ```

2. Rate Limiting
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @app.get("/query")
   @limiter.limit("100/minute")
   async def query_agent():
       # Your agent logic
   ```

3. Input Validation
   ```python
   from pydantic import BaseModel

   class QueryRequest(BaseModel):
       text: str
       agent: str
       max_length: int = 1000
   ```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Check environment variables
   echo $CLAUDE_API_KEY

   # Test API connectivity
   curl -H "x-api-key: $CLAUDE_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Hello"}' \
        https://api.anthropic.com/v1/messages
   ```

2. **Model Loading Errors**
   ```bash
   # Check GPU availability
   nvidia-smi

   # Monitor memory usage
   watch -n 1 nvidia-smi --query-gpu=memory.used,memory.total --format=csv
   ```

3. **Network Connectivity**
   ```bash
   # Test agent connectivity
   curl -X POST http://localhost:8000/transcribe \
        -F "audio=@test.wav" \
        -F "agent=claude"
   ```