"""
Database migration script to add OTP verification fields
Run this script to update the database schema
"""

from neurosight_app_with_auth import app, db
from models import User
from sqlalchemy import text

def migrate_add_otp_fields():
    """Add OTP verification fields to users table"""
    with app.app_context():
        try:
            # Add new columns
            with db.engine.connect() as conn:
                # Check if columns already exist
                result = conn.execute(text("PRAGMA table_info(users)"))
                existing_columns = [row[1] for row in result]
                
                columns_to_add = {
                    'email_verified': 'ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0',
                    'otp_code': 'ALTER TABLE users ADD COLUMN otp_code VARCHAR(6)',
                    'otp_expiry': 'ALTER TABLE users ADD COLUMN otp_expiry DATETIME',
                    'otp_attempts': 'ALTER TABLE users ADD COLUMN otp_attempts INTEGER DEFAULT 0'
                }
                
                added_count = 0
                for column_name, sql in columns_to_add.items():
                    if column_name not in existing_columns:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✓ Added column: {column_name}")
                        added_count += 1
                    else:
                        print(f"⊙ Column already exists: {column_name}")
                
                # Set email_verified = True for existing Google OAuth users
                conn.execute(text("""
                    UPDATE users 
                    SET email_verified = 1 
                    WHERE google_id IS NOT NULL AND email_verified IS NULL
                """))
                conn.commit()
                print("✓ Set email_verified=True for existing Google users")
                
                print(f"\n✅ Migration completed! Added {added_count} new columns.")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("  OTP VERIFICATION FIELDS MIGRATION")
    print("=" * 60)
    print("\nThis will add the following columns to the users table:")
    print("  - email_verified (BOOLEAN)")
    print("  - otp_code (VARCHAR(6))")
    print("  - otp_expiry (DATETIME)")
    print("  - otp_attempts (INTEGER)")
    print("\n" + "=" * 60)
    
    confirm = input("\nProceed with migration? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        migrate_add_otp_fields()
    else:
        print("\n❌ Migration cancelled.")
