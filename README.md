# ProcureSense

Enterprise Procurement Automation System with Advanced Context Engineering

## Overview

ProcureSense is a multi-agent procurement co-pilot that demonstrates advanced context engineering with enterprise alignment guarantees. The system uses configurable LLM providers (Ollama, OpenAI, etc.) to provide intelligent procurement assistance through specialized agents while maintaining strict policy compliance through a hierarchical, budgeted context architecture.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.template .env
   # Edit .env with your preferred deployment option
   ```

3. **Choose Deployment Option** (see Configuration section below)

4. **Run the Application**
   ```bash
   python -m src.main
   ```

## Configuration Options

### Option 1: Local Ollama with Smaller Model (Recommended)
- **Requirements**: 8GB+ RAM, 5GB+ storage
- **Setup**: 
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.ai/install.sh | sh
  
  # Pull smaller model
  ollama pull llama3.1:8b
  
  # Verify Ollama is running
  ollama run llama3.1:8b
  ```

### Option 2: Local Ollama with gpt-oss-20b
- **Requirements**: 16GB+ RAM, 40GB+ storage
- **Setup**:
  ```bash
  ollama pull gpt-oss-20b
  ollama run gpt-oss-20b
  ```

### Option 3: Remote Ollama Server
- Update `OLLAMA_HOST` in `.env` to point to your remote server

### Option 4: OpenAI-Compatible API
- Set `LLM_PROVIDER=openai` and configure API credentials in `.env`

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /agent/negotiation` - Negotiation agent (coming soon)
- `POST /agent/compliance` - Compliance agent (coming soon)
- `POST /agent/forecast` - Forecast agent (coming soon)

## Architecture

The system implements a layered context architecture with mathematical token budgeting:

- **Global Policy Context (GPC)** - 25% budget, never pruned
- **Domain Strategy Context (DSC)** - 25% budget, summarized
- **Task/Session Context (TSC)** - 40% budget, rolling summaries
- **Ephemeral Tool Context (ETC)** - 10% budget, first pruned

## Development

Run tests:
```bash
pytest tests/
```

Start development server:
```bash
uvicorn src.main:app --reload
```