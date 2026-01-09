import json
import os
import time
import random
import database  # Namma DB file
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- 1. SETUP GROQ ---
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
    else:
        client = None
except ImportError:
    client = None

# --- 2. CUSTOM TEMPLATES (Matches Your 5 Industries Exactly) ---
INDUSTRY_TEMPLATES = {
    "Technology": [
        # Targets: CTO, VP Eng, DevOps Lead
        {
            "subject": "Accelerating {company}'s deployment cycles",
            "body": "Hi {first_name},\n\nNoticed {company} is scaling fast. Often, rapid growth creates tech debt that slows down engineering velocity.\n\nWe help tech leaders automate CI/CD pipelines so your team focuses on shipping code, not fixing builds.\n\nOpen to a 15-min chat?\n\nBest,\nAshwin"
        },
        {
            "subject": "DevOps bottlenecks at {company}",
            "body": "Hi {first_name},\n\nAs a {role}, you know that manual ops work kills productivity. We allow engineering teams to self-serve infrastructure securely.\n\nWould love to show you how we reduce deployment time by 40%.\n\nBest,\nAshwin"
        }
    ],
    "Healthcare": [
        # Targets: Medical Director, Clinical Ops
        {
            "subject": "Patient data efficiency at {company}",
            "body": "Hi {first_name},\n\nI imagine data interoperability and patient experience are top priorities at {company}.\n\nWe help healthcare leaders automate patient intake forms securely, reducing admin workload by 20 hours/week.\n\nWorth a brief conversation?\n\nBest,\nAshwin"
        },
        {
            "subject": "Streamlining clinical ops",
            "body": "Hi {first_name},\n\nManaging clinical operations often means drowning in paperwork. It doesn't have to be that way.\n\nWe automate compliance checks and scheduling. Free for a 15-min demo?\n\nCheers,\nAshwin"
        }
    ],
    "Finance": [
        # Targets: CFO, Risk Manager, Compliance
        {
            "subject": "Risk mitigation at {company}",
            "body": "Hi {first_name},\n\nWith current market volatility, manual reconciliation is a huge risk for the {role}.\n\nOur AI automates financial reporting with 99.9% accuracy, ensuring you are audit-ready.\n\nCan we chat next week?\n\nBest,\nAshwin"
        },
        {
            "subject": "Automating {company}'s compliance",
            "body": "Hi {first_name},\n\nKeeping up with regulatory changes manually is tough. We help finance teams monitor transactions in real-time.\n\nWould love to share some insights on fraud detection.\n\nBest,\nAshwin"
        }
    ],
    "Retail": [
        # Targets: Head of E-commerce, Supply Chain, Brand
        {
            "subject": "Inventory optimization for {company}",
            "body": "Hi {first_name},\n\nBig fan of {company}. As the {role}, are stockouts or overstocking affecting your margins?\n\nWe help retail brands predict inventory needs using AI, cutting storage costs by 20%.\n\nOpen to a 15-min call?\n\nBest,\nAshwin"
        },
        {
            "subject": "{company}'s omnichannel experience",
            "body": "Hi {first_name},\n\nSaw your role as {role}. connecting online and offline data is often a headache.\n\nWe unify customer data to personalize shopping experiences automatically.\n\nWorth a quick chat?\n\nCheers,\nAshwin"
        }
    ],
    "Manufacturing": [
        # Targets: Plant Manager, Logistics Head
        {
            "subject": "Reducing downtime at {company}",
            "body": "Hi {first_name},\n\nReaching out to the {role} at {company}. Unplanned equipment downtime is costly.\n\nOur AI predicts maintenance needs before machines fail. Would love to show you how.\n\nBest,\nAshwin"
        },
        {
            "subject": "Supply chain visibility",
            "body": "Hi {first_name},\n\nOptimizing logistics and production flow is likely your priority. We automate supply chain tracking from raw material to delivery.\n\nFree for a call this week?\n\nBest,\nAshwin"
        }
    ],
    "Generic": [
        {
            "subject": "Growth at {company}",
            "body": "Hi {first_name},\n\nI've been following {company}'s growth. We use AI to automate manual workflows, saving teams 20+ hours a week.\n\nWorth a conversation?\n\nBest,\nAshwin"
        }
    ]
}

def get_smart_template(lead):
    """
    Selects a template based on industry keywords if AI fails.
    """
    try:
        first_name = lead.get('full_name', 'There').split()[0]
        company = lead.get('company_name', 'your company')
        role = lead.get('role', 'Leader')
        industry = lead.get('industry', 'Generic') # Direct match from DB
        
        # 1. Try Direct Match (Since our Generator produces exact names)
        templates = INDUSTRY_TEMPLATES.get(industry)
        
        # 2. If not found, Fallback to Keyword Match
        if not templates:
            raw_ind = industry.lower()
            if any(x in raw_ind for x in ["tech", "soft", "saas", "it", "data"]): category = "Technology"
            elif any(x in raw_ind for x in ["health", "med", "pharma"]): category = "Healthcare"
            elif any(x in raw_ind for x in ["fin", "bank", "invest"]): category = "Finance"
            elif any(x in raw_ind for x in ["retail", "brand", "commerce"]): category = "Retail"
            elif any(x in raw_ind for x in ["manufactur", "plant", "production"]): category = "Manufacturing"
            else: category = "Generic"
            templates = INDUSTRY_TEMPLATES.get(category)

        # Pick random template from the matched list
        tmpl = random.choice(templates)
        
        return {
            "email_variant_1": {
                "subject": tmpl["subject"].format(company=company, role=role, first_name=first_name),
                "body": tmpl["body"].format(company=company, role=role, first_name=first_name)
            },
            "email_variant_2": {
                "subject": f"Quick check on {company}",
                "body": f"Hi {first_name}, just following up. Open to a chat about automation? Best, Ashwin"
            },
            "linkedin_variant_1": f"Hi {first_name}, connecting to see how {company} is handling scale in the {industry} space.",
            "linkedin_variant_2": f"Hey {first_name}, huge fan of {company}. Would love to share how other {role}s are using AI."
        }
    except Exception:
        # Ultimate fallback
        return {
            "email_variant_1": {"subject": "Hello", "body": "Hi, let's connect."},
            "linkedin_variant_1": "Hi, let's connect."
        }

# --- 3. MAIN LOGIC ---
def generate_messages():
    print(f"Starting Message Generation (Groq + Templates)...")

    # 1. Connect to DB
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # 2. Fetch ENRICHED leads
    cursor.execute("SELECT * FROM leads WHERE status='ENRICHED'")
    rows = cursor.fetchall()
    
    if not rows:
        print("No ENRICHED leads found. Run Step 2 first.")
        conn.close()
        return

    print(f"Processing {len(rows)} leads...")

    processed_count = 0

    for row in rows:
        lead = dict(row) # Convert Row to Dict
        
        # Parse Pain Points
        pain_points = []
        if lead['pain_points']:
            try:
                pain_points = json.loads(lead['pain_points'])
            except:
                pain_points = []
        
        pain_points_str = ", ".join(pain_points)
        
        generated_msg = None
        source = "TEMPLATE"

        # --- A. TRY GROQ AI ---
        if client:
            try:
                # Rate limit safety
                time.sleep(1.2) 
                
                # STRICT PROMPT FOR ASSIGNMENT COMPLIANCE
                prompt = f"""
                Act as an SDR. Create cold outreach messages based on these details:
                Name: {lead['full_name']}
                Role: {lead['role']}
                Company: {lead['company_name']}
                Industry: {lead['industry']}
                Insights/Pain Points: {pain_points_str}

                ASSIGNMENT REQUIREMENTS (FOLLOW STRICTLY):
                1. GENERATE 4 MESSAGES: 
                   - Email Variant A
                   - Email Variant B
                   - LinkedIn DM Variant A
                   - LinkedIn DM Variant B
                
                2. CONTENT RULES:
                   - MUST reference the 'Insights/Pain Points' provided above.
                   - Email Length: MAXIMUM 120 words.
                   - LinkedIn DM Length: MAXIMUM 60 words.
                   - CTA: End emails with "Are you free for a 15-min call?".
                   - NO HALLUCINATIONS: Do not invent facts about the company not listed here.

                OUTPUT FORMAT:
                Return ONLY a valid JSON object with keys: 
                "email_variant_1" (object with subject, body), 
                "email_variant_2" (object with subject, body), 
                "linkedin_variant_1" (string), 
                "linkedin_variant_2" (string).
                """
                
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                generated_msg = json.loads(completion.choices[0].message.content)
                source = "AI (Groq)"
                print(f"AI Generated: {lead['full_name']}")
                
            except Exception as e:
                print(f"Groq Error ({e}). Switching to Template.")
                generated_msg = None
        
        # --- B. FALLBACK TO TEMPLATE ---
        if not generated_msg:
            generated_msg = get_smart_template(lead)
            source = "TEMPLATE"
            print(f"Template Used: {lead['full_name']}")

        # --- C. SAVE TO DB (UPDATE) ---
        msg_json = json.dumps(generated_msg)
        
        cursor.execute('''
            UPDATE leads 
            SET generated_messages=?, message_source=?, status='MESSAGED'
            WHERE id=?
        ''', (msg_json, source, lead['id']))
        
        processed_count += 1

    # 3. Commit Changes
    conn.commit()
    conn.close()
    
    print(f"Success! Generated messages for {processed_count} leads.")

if __name__ == "__main__":
    generate_messages()