# VoceChatBot

Multi-bot engine for [VoceChat](https://voce.chat) with Jellyfin, Jellyseerr and Ollama AI support.

## Bots

| Bot | Type | Description |
|-----|------|-------------|
| General | `ai_chat` | AI chatbot powered by Ollama (local LLM) |
| Jellyfin | `jellyfin_proxy` | Forwards Jellyfin notifications to a VoceChat channel |
| Jellyseerr | `jellyseerr_proxy` | Forwards Jellyseerr events + search/request commands |

## Quick Start

### 1. Create bots in VoceChat

Go to **Settings → Bot & Webhook** and create one bot per integration. Copy each bot's API key.

Set the webhook URL for each bot to point to this server:
- General: `https://your-server:8000/webhook/general`
- Jellyfin: `https://your-server:8000/webhook/jellyfin`
- Jellyseerr: `https://your-server:8000/webhook/jellyseerr`

### 2. Configure

```bash
cp config.yaml config.local.yaml
cp .env.example .env
# Edit config.local.yaml and .env with your values
```

### 3. Run with Docker Compose

```bash
# Using pre-built image
docker compose up -d

# Or build locally
docker compose up -d --build
```

### 4. Configure Jellyfin webhook

In Jellyfin: **Dashboard → Plugins → Webhook**

Add a webhook pointing to: `http://your-server:8000/webhook/jellyfin`  
Set the `x-api-key` header to your Jellyfin bot API key.

### 5. Configure Jellyseerr webhook

In Jellyseerr: **Settings → Notifications → Webhook**

URL: `http://your-server:8000/webhook/jellyseerr`  
Authorization header: `x-api-key: your-jellyseerr-bot-api-key`

## Configuration

All settings live in `config.yaml`. Secrets are referenced as `${ENV_VAR}` and injected from environment variables.

### AI Chatbot personality

Edit the `system_prompt` in `config.yaml` to change the bot's personality:

```yaml
bots:
  - name: "general"
    type: "ai_chat"
    config:
      model: "llama3.2"          # any model available in Ollama
      system_prompt: |
        You are a sarcastic but helpful butler named Jeeves...
      temperature: 0.9           # higher = more creative
      history_length: 20         # messages to remember per conversation
```

### Ollama

Make sure Ollama is running and the model is pulled:

```bash
ollama pull llama3.2
```

If running in Docker, set `ollama.base_url` in `config.yaml` to the Ollama host:

```yaml
ollama:
  base_url: "http://host.docker.internal:11434"
```

## Jellyseerr Commands

Users can chat with the Jellyseerr bot:

| Command | Description |
|---------|-------------|
| `!search <query>` | Search for movies or TV shows |
| `!request movie <tmdb_id>` | Request a movie |
| `!request tv <tmdb_id>` | Request a TV show |
| `!status` | Show recent requests |
| `!help` | Show available commands |

## Docker Image

Images are automatically built and published to GitHub Container Registry on every push to `main` and on version tags.

```bash
docker pull ghcr.io/jensmjahle/vocechatbot:latest
```

## Development

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Health check: `GET /health`
