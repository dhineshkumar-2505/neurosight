import sqlite3
import pandas as pd
import os

# Database path
db_path = 'instance/neurosight.db'

def view_data():
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found!")
        return

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        print("\n" + "="*50)
        print("👤 USERS TABLE")
        print("="*50)
        
        # Query users
        users_df = pd.read_sql_query("SELECT id, email, full_name, role, hospital, created_at FROM users", conn)
        if users_df.empty:
            print("No users found.")
        else:
            print(users_df.to_string(index=False))
            
        print("\n" + "="*50)
        print("📊 ANALYSIS HISTORY TABLE")
        print("="*50)
        
        # Query history
        history_df = pd.read_sql_query("""
            SELECT 
                h.id, 
                u.full_name as doctor,
                h.patient_name, 
                h.disease_type, 
                h.prediction, 
                h.confidence, 
                h.created_at 
            FROM analysis_history h
            JOIN users u ON h.user_id = u.id
            ORDER BY h.created_at DESC
        """, conn)
        
        if history_df.empty:
            print("No analysis history found.")
        else:
            print(history_df.to_string(index=False))
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")

if __name__ == "__main__":
    # Install pandas if needed
    try:
        import pandas
    except ImportError:
        print("Installing pandas for better visualization...")
        os.system('pip install pandas')
        
    view_data()
