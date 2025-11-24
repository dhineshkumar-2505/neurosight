"""
Database migration script for adding onboarding fields to User model
Run this script to update existing database without losing data
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Add new columns to users table"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'neurosight.db')
    db_uri = f'sqlite:///{db_path}'
    
    print(f"🔄 Starting database migration...")
    print(f"📁 Database: {db_path}")
    
    # Create engine
    engine = create_engine(db_uri)
    
    # Get inspector to check existing columns
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    print(f"\n📋 Existing columns: {len(existing_columns)}")
    
    # Define new columns to add
    new_columns = {
        'profile_photo_url': 'VARCHAR(500)',
        'medical_registration_no': 'VARCHAR(100)',
        'specialization': 'VARCHAR(100)',
        'years_of_experience': 'INTEGER',
        'clinic_timing': 'VARCHAR(255)',
        'hospital_id': 'VARCHAR(100)',
        'hospital_address': 'TEXT',
        'department': 'VARCHAR(100)',
        'hospital_logo_url': 'VARCHAR(500)',
        'hospital_phone': 'VARCHAR(20)',
        'onboarding_completed': 'BOOLEAN DEFAULT 0'
    }
    
    # Add columns that don't exist
    with engine.connect() as conn:
        columns_added = 0
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Added column: {column_name}")
                    columns_added += 1
                except Exception as e:
                    print(f"❌ Error adding {column_name}: {e}")
            else:
                print(f"⏭️  Column already exists: {column_name}")
        
        # Set onboarding_completed to False for existing Google OAuth users
        # (users with google_id but without onboarding_completed flag)
        try:
            update_sql = """
                UPDATE users 
                SET onboarding_completed = 0 
                WHERE google_id IS NOT NULL 
                AND onboarding_completed IS NULL
            """
            result = conn.execute(text(update_sql))
            conn.commit()
            print(f"\n🔄 Updated {result.rowcount} existing Google OAuth users to require onboarding")
        except Exception as e:
            print(f"⚠️  Warning updating existing users: {e}")
    
    print(f"\n✨ Migration completed! Added {columns_added} new columns.")
    print(f"📊 Total columns now: {len(existing_columns) + columns_added}")
    
    # Verify migration
    inspector = inspect(engine)
    final_columns = [col['name'] for col in inspector.get_columns('users')]
    print(f"\n✅ Verification: users table now has {len(final_columns)} columns")
    
    return True

def rollback_migration():
    """Remove added columns (use with caution!)"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'neurosight.db')
    db_uri = f'sqlite:///{db_path}'
    
    print(f"⚠️  WARNING: Rolling back migration...")
    print(f"📁 Database: {db_path}")
    
    response = input("Are you sure you want to rollback? This will remove data! (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Rollback cancelled")
        return False
    
    engine = create_engine(db_uri)
    
    # Note: SQLite doesn't support DROP COLUMN directly
    # You would need to recreate the table
    print("⚠️  SQLite doesn't support DROP COLUMN.")
    print("To rollback, you need to:")
    print("1. Backup your database")
    print("2. Delete the database file")
    print("3. Recreate it with the old schema")
    
    return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration for onboarding fields')
    parser.add_argument('--rollback', action='store_true', help='Rollback migration (dangerous!)')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        migrate_database()
