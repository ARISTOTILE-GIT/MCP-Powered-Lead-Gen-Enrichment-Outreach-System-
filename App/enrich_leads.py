import json
import random
import time
import os
import database # Namma DB file
from dotenv import load_dotenv

# Load Environment Variables (For AI Mode)
load_dotenv()

# Setup Groq (Optional - Only if AI mode is used)
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    client = None

def enrich_data(mode="offline"):
    print(f"Starting Enrichment (Mode: {mode})...")
    
    # 1. Connect to DB
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # 2. Fetch only 'NEW' leads
    cursor.execute("SELECT * FROM leads WHERE status='NEW'")
    rows = cursor.fetchall()
    
    if not rows:
        print("No NEW leads found to enrich.")
        conn.close()
        return

    print(f"Processing {len(rows)} leads...")
    
    for row in rows:
        # Convert DB Row to Dict
        lead = dict(row)
        lead_id = lead['id']
        industry = lead['industry']
        role = lead['role']
        company = lead['company_name']
        
        # --- ENRICHMENT LOGIC ---
        
        pain_points = []
        triggers = []
        persona = "Decision Maker"
        company_size = random.choice(["Mid-Market", "Enterprise", "Startup"])
        confidence = random.randint(75, 98)
        
        # A. AI MODE (Groq)
        if mode == "ai" and client:
            try:
                prompt = f"""
                Analyze this lead: Role: {role}, Industry: {industry}, Company: {company}.
                Return JSON with:
                - pain_points (list of 2 strings)
                - buying_triggers (list of 2 strings)
                """
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
                )
                data = json.loads(completion.choices[0].message.content)
                pain_points = data.get("pain_points", [])
                triggers = data.get("buying_triggers", [])
                print(f"AI Enriched: {lead['full_name']}")
                time.sleep(1) # Rate Limit Safety
                
            except Exception as e:
                print(f"AI Failed ({e}), falling back to Offline.")
                mode = "offline" # Fallback immediately for this lead

        # B. OFFLINE MODE (Fallback / Default)
        if not pain_points: # If AI failed or mode is offline
            if industry == "Technology":
                pain_points = ["Technical debt slowing down release cycles", "High cloud infrastructure costs"]
                triggers = ["Recent CTO hire", "Expanding engineering team"]
            elif industry == "Healthcare":
                pain_points = ["HIPAA compliance data silos", "Manual patient record processing"]
                triggers = ["New hospital wing opening", "Digitization initiative"]
            elif industry == "Finance":
                pain_points = ["Slow manual reconciliation processes", "Regulatory reporting errors"]
                triggers = ["Quarterly audit approaching", "Market expansion news"]
            else:
                pain_points = ["Operational inefficiencies", "Need for automation"]
                triggers = ["New leadership", "Cost cutting mandate"]
            
            print(f"Offline Enriched: {lead['full_name']}")
            time.sleep(0.1)

        # 3. SAVE TO DB (UPDATE)
        # Mukkiyam: Lists ah JSON String ah maathuraan (json.dumps)
        cursor.execute('''
            UPDATE leads 
            SET pain_points=?, 
                buying_triggers=?, 
                company_size=?, 
                persona=?, 
                confidence_score=?, 
                status='ENRICHED'
            WHERE id=?
        ''', (
            json.dumps(pain_points), 
            json.dumps(triggers), 
            company_size, 
            persona, 
            confidence, 
            lead_id
        ))

    # 4. Commit Changes
    conn.commit()
    conn.close()
    print("Enrichment Complete. Status updated to 'ENRICHED'.")

if __name__ == "__main__":
    # Test run
    enrich_data(mode="offline")