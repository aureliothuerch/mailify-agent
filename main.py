
import os
import sys
from services.imap_service import iCloudIMAPService
from agents.mail_graph import build_mail_graph

def main():
    print("=== 🤖 AI MAIL ARCHITECT STARTED ===")

    if not os.getenv("ICLOUD_EMAIL") or not os.getenv("ICLOUD_APP_PASSWORD"):
        print("❌ ERROR: ICLOUD_EMAIL or ICLOUD_APP_PASSWORD is not set!")
        print("Run in your terminal:")
        print("export ICLOUD_EMAIL='your@mail.com'")
        print("export ICLOUD_APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'")
        sys.exit(1)

    imap_service = iCloudIMAPService()

    raw_mail_data = imap_service.fetch_unread_email()

    if not raw_mail_data:
        print("\n[System] Inbox is clean. Nothing for the AI to do.")
        return

    initial_state = {
        "id": raw_mail_data["id"],
        "sender": raw_mail_data["sender"],
        "subject": raw_mail_data["subject"],
        "body": raw_mail_data["body"],
        "category": "",
        "reply_draft": ""
    }

    print("\n[System] Starting the LangGraph pipeline...")

    mail_agent = build_mail_graph()
    final_state = mail_agent.invoke(initial_state)

    print("\n==========================================")
    print(f"Result category: [{final_state['category']}]")
    print("==========================================")

    if final_state["category"] == "IMPORTANT" and final_state["reply_draft"]:
        imap_service.upload_draft(
            recipient=final_state["sender"],
            subject=final_state["subject"],
            text_content=final_state["reply_draft"]
        )
    else:
        print(f"No action required for category '{final_state['category']}'.")

    print("=== PROCESS FINISHED ===")

if __name__ == "__main__":
    main()
