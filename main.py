
import os
import sys
from services.imap_service import iCloudIMAPService
from agents.mail_graph import build_mail_graph

def main():
    print("=== AI MAIL ARCHITECT STARTED ===")

    if not os.getenv("ICLOUD_EMAIL") or not os.getenv("ICLOUD_APP_PASSWORD"):
        print("ERROR: ICLOUD_EMAIL or ICLOUD_APP_PASSWORD is not set!")
        print("Set env vars in an .env file or run in your terminal:")
        print("export ICLOUD_EMAIL='your@mail.com'")
        print("export ICLOUD_APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'")
        sys.exit(1)

    imap_service = iCloudIMAPService()

    raw_mails = imap_service.fetch_unread_emails()

    if not raw_mails:
        print("\n[System] Inbox is clean. Nothing for the AI to do.")
        return

    print(f"\n[System] Starting the LangGraph pipeline for {len(raw_mails)} mail(s)...")
    mail_agent = build_mail_graph()

    for i, raw in enumerate(raw_mails, 1):
        print(f"\n========== Mail {i}/{len(raw_mails)} ==========")
        final_state = mail_agent.invoke({
            "id": raw["id"],
            "sender": raw["sender"],
            "subject": raw["subject"],
            "body": raw["body"],
            "category": "",
            "reply_draft": ""
        })

        print(f"Result category: [{final_state['category']}]")

        if final_state["category"] == "IMPORTANT" and final_state["reply_draft"]:
            imap_service.upload_draft(
                recipient=final_state["sender"],
                subject=final_state["subject"],
                text_content=final_state["reply_draft"]
            )
        else:
            print(f"No action required for category '{final_state['category']}'.")

    print("\n=== PROCESS FINISHED ===")

if __name__ == "__main__":
    main()
