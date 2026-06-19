# Multi-Agent IT Support Voice Demo

This demo shows a multi-agent employee IT support flow:

- intake
- verification
- triage
- resolution
- escalation
- post-call review

ElevenLabs Conversational AI fits as the real-time voice layer. This repo provides:

- a simulated helpdesk backend
- a structured call-state engine
- a Streamlit demo dashboard
- a small set of IT runbooks
- API endpoints that ElevenLabs webhook tools can call
- optional Nebius-powered summarization, routing support, QA review, and escalation drafting

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the simulated helpdesk API:

```bash
uvicorn api:app --reload
```

Start the demo UI:

```bash
streamlit run app.py
```

Create a local `.env` file from the example template, then fill in your keys:

```bash
copy .env.example .env
```

Edit `.env` and add values like:

```env
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_AGENT_ID=your_elevenlabs_agent_id
ELEVENLABS_WEBHOOK_URL=https://your-public-url/webhooks/elevenlabs/post-call

NEBIUS_API_KEY=your_nebius_key
NEBIUS_MODEL=your_nebius_model
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
```

## ElevenLabs setup

Set these environment variables before running the app:

- `ELEVENLABS_API_KEY`
- `ELEVENLABS_AGENT_ID`
- `ELEVENLABS_WEBHOOK_URL`

Use the FastAPI endpoints as webhook targets for ElevenLabs tools:

- `POST /employees/verify`
- `GET /incidents/{category}`
- `POST /tickets`
- `POST /webhooks/elevenlabs/post-call`

Upload the runbooks in `runbooks/` to the ElevenLabs knowledge base, then enable RAG on the agent.

For the live voice flow, create an ElevenLabs agent that:

- handles intake
- calls the verification and ticket tools
- uses the knowledge base for troubleshooting
- transfers to escalation when needed

The Streamlit app reads the ElevenLabs settings from the environment and shows them in the sidebar as read-only status. It remains the presentation layer for the demo and the post-call review.

## Nebius setup

If you want backend AI assistance for routing, call summaries, QA review, and escalation drafting, set:

- `NEBIUS_API_KEY`
- `NEBIUS_MODEL`
- `NEBIUS_BASE_URL`

When those are present, the backend will use Nebius for:

- transcript summarization
- routing support
- QA review
- escalation drafting

If the Nebius settings are empty, the app falls back to deterministic local logic.

## Call Flow

```mermaid
flowchart LR
    A[Caller] --> B[Intake Agent]
    B --> C[Verification Agent]
    C --> D[Triage Agent]

    D -->|Known incident| E[Escalation Agent]
    D -->|Individual issue| F[Resolution Agent]

    F -->|Resolved| G[Post-Call Review]
    F -->|Not resolved| E
    E --> G

    G --> H[Demo Dashboard]

    subgraph Runtime["Runtime Layer"]
      B
      C
      D
      E
      F
      G
    end

    subgraph Backend["Simulated Backend + KB"]
      I[Employee Directory]
      J[Incident Feed]
      K[Ticketing API]
      L[Runbook Knowledge Base]
    end

    C -. lookup .-> I
    D -. check .-> J
    E -. create .-> K
    F -. retrieve .-> L
```

At a glance:

- The caller enters through the voice experience.
- Intake, verification, triage, resolution, and escalation are the active agents.
- The post-call review stage produces the QA summary.
- The demo dashboard shows the transcript, handoffs, and review outcome.

## Architecture

```mermaid
flowchart TB
    Caller[Employee Caller] --> ElevenLabs[ElevenLabs Voice Agents]
    ElevenLabs --> KB[Runbook Knowledge Base]
    ElevenLabs --> API[FastAPI Helpdesk API]
    API --> UI[Streamlit Demo App]
    API --> Review[Post-Call Review]
```

This is the simplest way to think about the system:

- ElevenLabs runs the live conversation and agent handoffs.
- The FastAPI app simulates the helpdesk systems and receives the post-call webhook.
- The Streamlit app presents the live demo and structured review.
- The API endpoints behind the diagram are `POST /employees/verify`, `GET /incidents/{category}`, `POST /tickets`, and `POST /webhooks/elevenlabs/post-call`.
