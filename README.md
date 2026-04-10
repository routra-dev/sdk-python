# Routra Python SDK

Thin wrapper over the [OpenAI Python SDK](https://github.com/openai/openai-python). Adds typed routing metadata, policy helpers, and async support.

## Installation

```bash
pip install routra
# or
uv add routra
```

## Quick Start

```python
from routra import Routra

client = Routra(api_key="rtr-...")
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Hello"}],
)

# Typed routing metadata on every non-streaming response
if response.routra:
    print(response.routra.provider)    # "groq"
    print(response.routra.latency_ms)  # 245
    print(response.routra.score)       # 0.8642
    print(response.routra.cost_usd)    # 0.000089
```

## Routing Policies

```python
# Set a default policy for all requests
client = Routra(api_key="rtr-...", policy="cheapest")

# Per-request policy override
fast_client = client.with_policy("fastest")
response = fast_client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Urgent request"}],
)
```

## Async Support

```python
from routra import AsyncRoutra

client = AsyncRoutra(api_key="rtr-...")
response = await client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.routra.provider)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ROUTRA_API_KEY` | Default API key (used when `api_key` parameter is not provided) |
| `ROUTRA_BASE_URL` | Override API base URL (default: `https://api.routra.dev/v1`) |

```python
import os
os.environ["ROUTRA_API_KEY"] = "rtr-..."

# No need to pass api_key
client = Routra()
```

## Routing Metadata

The `response.routra` field is a `RoutingMetadata` object with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `provider` | `str` | Provider slug that served the request (e.g. `"groq"`) |
| `latency_ms` | `int` | Total provider response time in milliseconds |
| `score` | `float` | Normalized routing score (0–1) |
| `cost_usd` | `float \| None` | Estimated cost in USD |
| `input_tokens` | `int \| None` | Input token count |
| `output_tokens` | `int \| None` | Output token count |
| `failover` | `bool \| None` | Whether the request was rerouted due to a provider failure |
| `ttfb_ms` | `int \| None` | Time to first byte (streaming only) |

> **Note:** `routra` metadata is only available on non-streaming responses. For streaming, use the `x-routra-provider` response header.

## Multimodal Routing

All OpenAI-compatible endpoints are proxied through Routra — use the same client for chat, embeddings, images, TTS, and STT with automatic cost routing:

```python
# Image — routes to cheapest: FLUX Schnell ($0.001) vs GPT Image 1.5 ($0.13)
image = client.images.generate(
    model="auto:image",
    prompt="a sunset over mountains",
    size="1024x1024",
)

# TTS — voice passthrough, streaming supported
audio = client.audio.speech.create(
    model="auto:tts",
    input="Hello, welcome to our service.",
    voice="alloy",
)

# STT — multipart form-data forwarded transparently
transcript = client.audio.transcriptions.create(
    model="auto:stt",
    file=open("audio.mp3", "rb"),
)
```

Use `auto:image`, `auto:tts`, `auto:stt` for cheapest routing, or pin a provider with `model="openai/gpt-image-1.5"` or `model="fireworks/flux-1-schnell"`.

## OpenAI Compatibility

Since `Routra` extends `openai.OpenAI`, all OpenAI SDK features work transparently:

```python
# Streaming (metadata via headers, not response object)
stream = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")

# Embeddings
embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input="Hello world",
)

# Image Generation — auto-routes to cheapest provider
image = client.images.generate(
    model="auto:image",  # FLUX Schnell ($0.001) vs GPT Image 1.5 ($0.13)
    prompt="a sunset over mountains",
    size="1024x1024",
)

# Text-to-Speech
audio = client.audio.speech.create(
    model="auto:tts",
    input="Hello, welcome to our service.",
    voice="alloy",
)

# Speech-to-Text
transcript = client.audio.transcriptions.create(
    model="auto:stt",
    file=open("audio.mp3", "rb"),
)
```

## License

MIT
