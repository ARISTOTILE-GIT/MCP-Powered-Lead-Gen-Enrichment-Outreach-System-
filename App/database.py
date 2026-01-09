import sqlite3
import json
import os

# Database File Name
DB_NAME = "leads.db"

def get_db_connection():
    """
    Creates a connection to the SQLite database.
    check_same_thread=False is needed for FastAPI/Streamlit.
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    # Idhu romba mukkiyam! Row factory ah set panrom.
    # Idhunaala namma column names vachi data edukalam (Dict maari work aagum).
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """
    Initializes the database table if it doesn't exist.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Table with all necessary columns
    # JSON Data (lists/dicts) will be stored as TEXT (Strings)
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            full_name TEXT,
            company_name TEXT,
            role TEXT,
            industry TEXT,
            website TEXT,
            email TEXT,
            linkedin_url TEXT,
            country TEXT,
            status TEXT DEFAULT 'NEW',
            
            -- Enrichment Fields (Stored as JSON Strings)
            pain_points TEXT, 
            buying_triggers TEXT, 
            company_size TEXT,
            persona TEXT,
            confidence_score INTEGER,
            
            -- Message Fields (Stored as JSON Strings)
            generated_messages TEXT, 
            message_source TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_NAME}")

# Helper function to convert DB Row to Dictionary (API response ku useful)
def row_to_dict(row):
    return dict(row)

# Run this once if file is executed directly
if __name__ == "__main__":
    # Remove old DB if you want a fresh start (Optional)
    # if os.path.exists(DB_NAME): os.remove(DB_NAME)
    init_db()