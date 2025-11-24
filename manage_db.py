import sqlite3
import os

# Database path
db_path = 'instance/neurosight.db'

def manage_db():
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    while True:
        print("\n" + "="*40)
        print("🛠️  DATABASE MANAGER")
        print("="*40)
        print("1. View Users")
        print("2. Delete a User (by Email)")
        print("3. View Analysis History")
        print("4. Clear All Analysis History")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")

        if choice == '1':
            cursor.execute("SELECT id, email, full_name FROM users")
            users = cursor.fetchall()
            print("\n--- Users ---")
            for u in users:
                print(f"ID: {u[0]} | Email: {u[1]} | Name: {u[2]}")
        
        elif choice == '2':
            email = input("Enter email of user to delete: ")
            cursor.execute("DELETE FROM users WHERE email = ?", (email,))
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ User '{email}' deleted successfully.")
            else:
                print(f"❌ User '{email}' not found.")

        elif choice == '3':
            cursor.execute("SELECT id, patient_name, disease_type, prediction FROM analysis_history")
            history = cursor.fetchall()
            print("\n--- Analysis History ---")
            for h in history:
                print(f"ID: {h[0]} | Patient: {h[1]} | Disease: {h[2]} | Result: {h[3]}")

        elif choice == '4':
            confirm = input("Are you sure you want to delete ALL history? (yes/no): ")
            if confirm.lower() == 'yes':
                cursor.execute("DELETE FROM analysis_history")
                conn.commit()
                print("✅ All analysis history cleared.")
            else:
                print("Operation cancelled.")

        elif choice == '5':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")

    conn.close()

if __name__ == "__main__":
    manage_db()
