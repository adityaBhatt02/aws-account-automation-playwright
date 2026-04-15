import imaplib
import email
import ssl
import certifi
import re
from bs4 import BeautifulSoup


def get_email_otp_simple(email_address, app_password):
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993, ssl_context=context)
        mail.login(email_address, app_password)
        print(f"✅ Logged into {email_address}")

        mail.select("inbox")

        # 🔥 FIX: get ALL emails instead of strict filter
        status, data = mail.search(None, 'UNSEEN')

        if status != "OK" or not data[0]:
            print("[INFO] No UNSEEN emails, checking ALL...")
            status, data = mail.search(None, 'ALL')

        if status != "OK" or not data[0]:
            print("[INFO] No emails found at all")
            return None

        email_ids = data[0].split()

        # 🔥 Check last 10 emails (instead of 3)
        for latest_id in reversed(email_ids[-10:]):
            status, msg_data = mail.fetch(latest_id, "(RFC822)")
            if status != "OK":
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # 🔥 NEW: flexible AWS filter
            from_ = msg.get("From", "").lower()
            subject = msg.get("Subject", "").lower()

            print(f"[DEBUG] From: {from_}")
            print(f"[DEBUG] Subject: {subject}")

            if not any(k in from_ for k in ["amazon", "aws", "signin"]):
                continue

            # ⏱️ Email age check
            from email.utils import parsedate_to_datetime
            import datetime

            try:
                date_str = msg.get("Date")
                email_time = parsedate_to_datetime(date_str)
                now = datetime.datetime.now(datetime.timezone.utc)
                age_minutes = (now - email_time).total_seconds() / 60

                if age_minutes > 10:
                    print(f"[INFO] Email too old ({age_minutes:.1f} min), skipping")
                    continue

                print(f"[INFO] Email age: {age_minutes:.1f} minutes")

            except Exception as e:
                print(f"[WARN] Could not parse email date: {e}")

            text = ""
            html_text = ""

            if msg.is_multipart():
                for part in msg.walk():
                    try:
                        ct = part.get_content_type()
                        payload = part.get_payload(decode=True)
                        if not payload:
                            continue

                        decoded = payload.decode("utf-8", "ignore")

                        if ct == "text/html":
                            soup = BeautifulSoup(decoded, "html.parser")
                            html_text += soup.get_text() + "\n"

                        elif ct == "text/plain":
                            text += decoded + "\n"

                    except:
                        pass
            else:
                text = msg.get_payload(decode=True).decode("utf-8", "ignore")

            # Prefer plain text, fallback to HTML
            search_text = text if text.strip() else html_text
            clean_text = search_text.replace("\n", " ").replace("\r", " ")

            print(f"[DEBUG] Extracted text snippet: {clean_text[:300]}")

            # 🔥 Extract OTP
            matches = re.findall(r"\b(\d{6})\b", clean_text)

            if matches:
                otp = matches[-1]
                print(f"✅ OTP FOUND: {otp}")

                mail.store(latest_id, '+FLAGS', '\\Seen')
                return otp

        print("❌ OTP not found in recent emails")
        return None

    except Exception as e:
        print("❌ Email error:", e)
        import traceback
        traceback.print_exc()
        return None