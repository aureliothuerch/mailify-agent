import requests
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
import os


class EmailState(TypedDict):
    id: str
    sender: str
    subject: str
    body: str
    category: str
    reply_draft: str


def classify_node(state: EmailState) -> dict:
    """STATION 1: Figures out what the email is about."""
    print(f"\n[Pipeline - Station 1] AI analyzing mail from: {state['sender']}")

    prompt = f"""
    Du bist ein präziser E-Mail-Sortier-Assistent.
    Analysiere den Betreff und den Inhalt der folgenden E-Mail.
    Antworte AUSSCHLIESSLICH mit einem einzigen Wort aus dieser Liste:
    - IMPORTANT (Persönliche Mails, konkrete Anfragen, Familie, Chef)
    - SUPPORT (Rechnungen, Abos, Kündigungen, Bestellbestätigungen)
    - NEWSLETTER (Updates, Tech-News, Marketing-Mails, GitHub)
    - SPAM (Unerwünschte Werbung, Phishing, Betrug)

    Betreff: {state['subject']}
    Inhalt: {state['body']}

    Kategorie:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": os.getenv("MODEL"), "prompt": prompt, "stream": False},
            timeout=30
        )
        result = response.json()["response"].strip().upper()

        valid_categories = ["IMPORTANT", "SUPPORT", "NEWSLETTER", "SPAM"]
        final_category = "UNKNOWN"

        for cat in valid_categories:
            if cat in result:
                final_category = cat
                break

        print(f"[Pipeline - Station 1] AI decision: -> {final_category} <-")
        return {"category": final_category}

    except Exception as e:
        print(f"[Pipeline - Station 1] Ollama connection error: {e}")
        return {"category": "NEWSLETTER"}


def draft_node(state: EmailState) -> dict:
    """STATION 2: Writes a reply draft for important emails."""
    print("[Pipeline - Station 2] AI writing a reply draft...")

    prompt = f"""
    Schreibe eine kurze, höfliche und professionelle Antwort auf Deutsch für diese E-Mail.
    Gehe kurz auf das Anliegen ein. Signiere mit 'Dein KI-Assistent'.

    E-Mail von: {state['sender']}
    Betreff: {state['subject']}
    Inhalt: {state['body']}

    Antwort-Entwurf:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": os.getenv("MODEL"), "prompt": prompt, "stream": False},
            timeout=30
        )
        draft = response.json()["response"].strip()
        return {"reply_draft": draft}
    except Exception as e:
        return {"reply_draft": f"Error creating the draft: {e}"}


def routing_logic(state: EmailState) -> str:
    if state["category"] == "IMPORTANT":
        return "to_draft"
    return "to_end"


def build_mail_graph():
    builder = StateGraph(EmailState)

    builder.add_node("classify", classify_node)
    builder.add_node("draft", draft_node)

    builder.add_edge(START, "classify")

    builder.add_conditional_edges(
        "classify",
        routing_logic,
        {
            "to_draft": "draft",
            "to_end": END
        }
    )

    builder.add_edge("draft", END)

    return builder.compile()
