import smtplib
import json
import time
import logging
import sys
import database  # Namma DB file
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
SMTP_SERVER = "localhost"
SMTP_PORT = 1025  # Make sure mock_server.py is running!
MAX_RETRIES = 2
MESSAGES_PER_MINUTE = 60 # Assignment Demo Speed
DELAY_BETWEEN_MSGS = 60 / MESSAGES_PER_MINUTE 

# --- SETUP LOGGING ---
# Assignment Condition: "Error handling with structured logs"
logging.basicConfig(
    filename='outreach.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

# Fix for Windows Emoji Crash (Safety)
# Windows terminal la emoji print panna crash aagama irukka
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def send_email_with_retry(to_email, subject, body, retries=MAX_RETRIES):
    """
    Sends email via Local Mock SMTP Server.
    Includes Retry Logic (Assignment Condition).
    """
    attempt = 0
    while attempt <= retries:
        try:
            msg = MIMEMultipart()
            msg['From'] = "me@agentic-ai.com"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
            return True 
        except Exception as e:
            print(f"      ⚠️ SMTP Error: {e}. Retrying ({attempt+1}/{retries})...")
            attempt += 1
            time.sleep(1) # Wait before retry
    return False 

def process_sending(mode="dry_run"):
    print(f"🚀 Starting Multi-Channel Sending (Mode: {mode})...")
    
    # 1. Connect to DB
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # 2. Fetch leads ready to send (Only 'MESSAGED' status)
    cursor.execute("SELECT * FROM leads WHERE status='MESSAGED'")
    rows = cursor.fetchall()
    
    if not rows:
        print("⚠️ No MESSAGED leads found. Please generate messages first.")
        conn.close()
        return

    print(f"📊 Found {len(rows)} leads ready to send.")

    sent_count = 0

    for i, row in enumerate(rows):
        lead = dict(row)
        
        # Parse Messages (Stored as JSON String in DB)
        try:
            msgs = json.loads(lead['generated_messages'])
        except:
            msgs = {}

        # Pick Variant 1 (Default for automation)
        email_data = msgs.get("email_variant_1", {})
        linkedin_msg = msgs.get("linkedin_variant_1", "Hi, let's connect.")
        
        print(f"\n[{i+1}/{len(rows)}] 👤 {lead['full_name']} ({lead['company_name']})")

        # --- CHANNEL 1: EMAIL (SMTP) ---
        email_status = "SKIPPED"
        if mode == "live":
            # Assignment Condition: Send via SMTP
            success = send_email_with_retry(lead['email'], email_data.get("subject", "Hello"), email_data.get("body", "Body"))
            if success:
                print(f"   📧 Email: ✅ Sent (via Mock Server)")
                logging.info(f"EMAIL SENT to {lead['full_name']} <{lead['email']}>")
                email_status = "SENT"
            else:
                print(f"   📧 Email: ❌ Failed (Max Retries Exceeded)")
                logging.error(f"EMAIL FAILED for {lead['full_name']}")
                email_status = "FAILED"
        else:
            print(f"   📧 Email: 📝 Dry Run Logged (Subject: {email_data.get('subject')})")
            email_status = "DRY_RUN"

        # --- CHANNEL 2: LINKEDIN (Simulation) ---
        # Assignment Condition: "LinkedIn DM should be simulated"
        if mode == "live":
            time.sleep(0.5) # Simulate typing delay
            print(f"   🔗 LinkedIn: ✅ DM Sent (Simulated)")
            logging.info(f"LINKEDIN DM SENT to {lead['full_name']}: {linkedin_msg[:30]}...")
        else:
            print(f"   🔗 LinkedIn: 📝 Dry Run Logged")

        # --- UPDATE DB STATUS ---
        # If email failed, mark whole lead as failed, else SENT
        final_status = "SENT" if mode == "live" and email_status == "SENT" else "SENT_DRY_RUN"
        if email_status == "FAILED": final_status = "FAILED"

        cursor.execute("UPDATE leads SET status=? WHERE id=?", (final_status, lead['id']))
        sent_count += 1

        # Rate Limit Delay (Assignment Condition)
        if mode == "live" and i < len(rows) - 1:
            time.sleep(DELAY_BETWEEN_MSGS)

    # 3. Commit & Close
    conn.commit()
    conn.close()
    print(f"\n🎉 Done! Processed {sent_count} leads.")
    print(f"📄 Check 'outreach.log' for detailed history.")

if __name__ == "__main__":
    # Defaulting to dry_run for safety when running manually
    # Use "live" to actually hit the mock server
    process_sending(mode="live")