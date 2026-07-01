# Mailify Agent

A **100% local, privacy-first email triage agent**. It reads an unread email over
IMAP, classifies it with a self-hosted LLM, and — only for important mail — drafts
a reply and saves it back to your Drafts folder. No cloud APIs, no third-party
inference, no email content ever leaves your machine.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) for the agent
pipeline and [Ollama](https://ollama.com) for local model inference.

> **Why local-only?** Email is sensitive. This project deliberately runs every
> inference step on-premise against open-source models. Swapping in a cloud LLM
> would be one line — the point is that you never have to.

---

## How it works

```
                 ┌──────────────┐
   IMAP inbox ──▶│  fetch mail  │   pull oldest UNSEEN email
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  classify    │   local LLM → IMPORTANT | SUPPORT | NEWSLETTER | SPAM
                 └──────┬───────┘
              IMPORTANT │ else
                        ▼               ▼
                 ┌──────────────┐    (end)
                 │  draft reply │   local LLM writes a polite reply
                 └──────┬───────┘
                        ▼
                 IMAP Drafts folder
```

The graph is defined in [`agents/mail_graph.py`](agents/mail_graph.py). A conditional
edge routes only `IMPORTANT` mail to the drafting node; everything else terminates
early to save compute.

## Features

- **Fully offline inference** — models run through a local Ollama server (`localhost:11434`).
- **Agentic pipeline** — classify → route → draft, as an explicit LangGraph state machine.
- **Safe classification** — output is validated against a fixed category set; unknown responses fall back gracefully instead of trusting raw model text.
- **Human-in-the-loop by design** — the agent never sends mail. It writes a *draft* you review in your normal mail client.
- **Model-agnostic** — point it at any Ollama-served model via one env var.

## Requirements

- Python 3.10+
- A running [Ollama](https://ollama.com) instance with a pulled model, e.g. `ollama pull llama3`
- An IMAP mailbox (currently tuned for iCloud — see [Limitations](#limitations))

## Quickstart

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Start your local model
ollama pull llama3
ollama serve            # if not already running

# 3. Configure (environment variables)
export ICLOUD_EMAIL='your@icloud.com'
export ICLOUD_APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'   # app-specific password, not your Apple ID password
export MODEL='llama3'

# 4. Run
python main.py
```

Each run processes the single oldest unread email. Run it on a loop or a cron/systemd
timer to keep the inbox triaged.

## Configuration

| Variable              | Description                                             |
|-----------------------|---------------------------------------------------------|
| `ICLOUD_EMAIL`        | Your iCloud email address                               |
| `ICLOUD_APP_PASSWORD` | An [app-specific password](https://support.apple.com/en-us/102654) |
| `MODEL`               | Ollama model tag to use (e.g. `llama3`, `mistral`)      |

## Project structure

```
main.py                    entrypoint: fetch → run graph → upload draft
agents/mail_graph.py       LangGraph pipeline (state, nodes, routing)
services/imap_service.py   IMAP client: fetch unread, upload draft
requirements.txt
```

## Limitations

- **IMAP is tuned for iCloud** (server host + the `\Draft` flag quirk Apple requires).
  Generalizing to Gmail/Outlook/any IMAP host is mostly a config change in
  [`services/imap_service.py`](services/imap_service.py).
- Processes one email per invocation (intentional — keeps each run cheap and observable).
- Classification prompts and generated replies are in German; adjust the prompts in
  [`agents/mail_graph.py`](agents/mail_graph.py) for other languages.

## Roadmap

- [ ] Configurable IMAP provider (host + folder names) instead of hard-coded iCloud
- [ ] Batch processing with concurrency limits
- [ ] Structured logging + basic metrics (latency per node, tokens, category counts)
- [ ] Pluggable inference backend (Ollama today; vLLM / SGLang for higher throughput)

## License

Open source — MIT.
