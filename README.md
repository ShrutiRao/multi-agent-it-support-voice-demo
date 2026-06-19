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

## ElevenLabs setup

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

The Streamlit app is the presentation layer for the demo and the post-call review.

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
