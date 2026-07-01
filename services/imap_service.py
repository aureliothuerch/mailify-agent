import os
import imaplib
import email
from email.header import decode_header

class iCloudIMAPService:
    def __init__(self):
        self.email_address = os.getenv("ICLOUD_EMAIL")
        self.app_password = os.getenv("ICLOUD_APP_PASSWORD")
        self.imap_server = "imap.mail.me.com"
        self.mail = None

        if not self.email_address or not self.app_password:
            raise ValueError(
                "❌ ERROR: ICLOUD_EMAIL or ICLOUD_APP_PASSWORD was not set in the terminal!\n"
                "Use: export ICLOUD_EMAIL='your@mail.com' && export ICLOUD_APP_PASSWORD='xxxx-xxxx-xxxx-xxxx'"
            )

    def connect(self):
        if not self.mail:
            print(f"[IMAP] Connecting to iCloud for {self.email_address}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.app_password)

    def disconnect(self):
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass
            self.mail = None

    def fetch_unread_email(self) -> dict | None:
        """Fetches the oldest unread email and returns it in structured form."""
        try:
            self.connect()
            self.mail.select("inbox")

            status, response_data = self.mail.search(None, 'UNSEEN')
            mail_ids = response_data[0].split()

            if not mail_ids:
                print("[IMAP] No unread emails in the inbox.")
                return None

            target_id = mail_ids[0]
            status, data = self.mail.fetch(target_id, '(RFC822)')

            raw_content = data[0][1]
            msg = email.message_from_bytes(raw_content)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            sender = msg.get("From")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        body = payload.decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            print(f"[IMAP] Successfully loaded: '{subject}'")

            return {
                "id": target_id.decode(),
                "sender": sender,
                "subject": subject,
                "body": body.strip()
            }

        except Exception as e:
            print(f"[IMAP] Error fetching the mail: {e}")
            return None
        finally:
            self.disconnect()

    def upload_draft(self, recipient: str, subject: str, text_content: str):
        """Creates a real email in the iCloud 'Drafts' folder."""
        print(f"[IMAP] Uploading AI reply draft for {recipient}...")

        try:
            self.connect()

            from email.mime.text import MIMEText
            from email.utils import formatdate
            import time

            msg = MIMEText(text_content, "plain", "utf-8")
            msg["Subject"] = f"Re: {subject}"
            msg["From"] = self.email_address
            msg["To"] = recipient
            msg["Date"] = formatdate(time.time(), localtime=True)

            # iCloud requires the system folder "Drafts" and the '\Draft' flag
            self.mail.append(
                "Drafts",
                r"(\Draft)",
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes()
            )
            print("[IMAP] Draft successfully saved to iCloud! 🎉 (Check your Apple Mail app)")

        except Exception as e:
            print(f"[IMAP] Error uploading the draft: {e}")
        finally:
            self.disconnect()
