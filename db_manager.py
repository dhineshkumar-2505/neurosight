"""
Database Manager - Interactive tool to manage NeuroSight users
Run this script to add, view, update, or delete users from the database
"""

from neurosight_app_with_auth import app, db
from models import User
from werkzeug.security import generate_password_hash
import sys


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def list_all_users():
    """Display all users in the database"""
    print_header("ALL USERS")
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"\nTotal Users: {len(users)}\n")
        for i, user in enumerate(users, 1):
            print(f"{i}. ID: {user.id}")
            print(f"   Name: {user.full_name or 'N/A'}")
            print(f"   Email: {user.email}")
            print(f"   Google ID: {user.google_id or 'N/A'}")
            print(f"   Onboarding: {'✓ Complete' if user.onboarding_completed else '✗ Incomplete'}")
            print(f"   Specialization: {user.specialization or 'N/A'}")
            print(f"   Hospital: {user.hospital or 'N/A'}")
            print(f"   Created: {user.created_at}")
            print("-" * 60)


def search_user():
    """Search for a user by email"""
    print_header("SEARCH USER")
    email = input("\nEnter email to search: ").strip()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"\n❌ No user found with email: {email}")
            return
        
        print(f"\n✓ User Found:")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.full_name or 'N/A'}")
        print(f"   Email: {user.email}")
        print(f"   Google ID: {user.google_id or 'N/A'}")
        print(f"   Phone: {user.phone or 'N/A'}")
        print(f"   Medical Reg No: {user.medical_registration_no or 'N/A'}")
        print(f"   Specialization: {user.specialization or 'N/A'}")
        print(f"   Years of Experience: {user.years_of_experience or 'N/A'}")
        print(f"   Hospital: {user.hospital or 'N/A'}")
        print(f"   Hospital ID: {user.hospital_id or 'N/A'}")
        print(f"   Department: {user.department or 'N/A'}")
        print(f"   Onboarding Complete: {user.onboarding_completed}")
        print(f"   Created: {user.created_at}")
        print(f"   Updated: {user.updated_at}")


def delete_user():
    """Delete a user by email"""
    print_header("DELETE USER")
    email = input("\nEnter email of user to delete: ").strip()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"\n❌ No user found with email: {email}")
            return
        
        print(f"\n⚠️  WARNING: You are about to delete:")
        print(f"   Name: {user.full_name or 'N/A'}")
        print(f"   Email: {user.email}")
        
        confirm = input("\nType 'DELETE' to confirm: ").strip()
        
        if confirm == 'DELETE':
            db.session.delete(user)
            db.session.commit()
            print(f"\n✓ User '{email}' has been deleted successfully!")
        else:
            print("\n❌ Deletion cancelled.")


def delete_all_users():
    """Delete all users from the database"""
    print_header("DELETE ALL USERS")
    
    with app.app_context():
        count = User.query.count()
        
        if count == 0:
            print("\nNo users to delete.")
            return
        
        print(f"\n⚠️  WARNING: You are about to delete ALL {count} users!")
        confirm = input("\nType 'DELETE ALL' to confirm: ").strip()
        
        if confirm == 'DELETE ALL':
            User.query.delete()
            db.session.commit()
            print(f"\n✓ All {count} users have been deleted successfully!")
        else:
            print("\n❌ Deletion cancelled.")


def delete_users_by_ids():
    """Delete multiple users by their IDs"""
    print_header("BULK DELETE BY IDs")
    
    with app.app_context():
        # First, show all users with their IDs
        users = User.query.all()
        
        if not users:
            print("\nNo users found in the database.")
            return
        
        print(f"\nAvailable Users:\n")
        for user in users:
            print(f"ID: {user.id:3d} | {user.email:40s} | {user.full_name or 'N/A'}")
        
        print("\n" + "-" * 60)
        print("Enter user IDs to delete (comma-separated)")
        print("Example: 1,3,5 or 1, 2, 3")
        ids_input = input("\nUser IDs: ").strip()
        
        if not ids_input:
            print("\n❌ No IDs provided. Deletion cancelled.")
            return
        
        # Parse IDs
        try:
            user_ids = [int(id.strip()) for id in ids_input.split(',')]
        except ValueError:
            print("\n❌ Invalid input. Please enter numbers separated by commas.")
            return
        
        # Find users to delete
        users_to_delete = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users_to_delete:
            print("\n❌ No users found with the provided IDs.")
            return
        
        # Show users to be deleted
        print(f"\n⚠️  WARNING: You are about to delete {len(users_to_delete)} user(s):")
        for user in users_to_delete:
            print(f"   ID: {user.id} - {user.email} ({user.full_name or 'N/A'})")
        
        # Confirm deletion
        confirm = input(f"\nType 'DELETE' to confirm deletion of {len(users_to_delete)} user(s): ").strip()
        
        if confirm == 'DELETE':
            deleted_count = 0
            for user in users_to_delete:
                db.session.delete(user)
                deleted_count += 1
            
            db.session.commit()
            print(f"\n✓ Successfully deleted {deleted_count} user(s)!")
            
            # Show which IDs were not found (if any)
            found_ids = [user.id for user in users_to_delete]
            not_found = [id for id in user_ids if id not in found_ids]
            if not_found:
                print(f"\n⚠️  Note: The following IDs were not found: {', '.join(map(str, not_found))}")
        else:
            print("\n❌ Deletion cancelled.")



def add_test_user():
    """Add a test user to the database"""
    print_header("ADD TEST USER")
    
    print("\nEnter user details (press Enter to skip optional fields):")
    
    email = input("Email* (required): ").strip()
    if not email:
        print("❌ Email is required!")
        return
    
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"\n❌ User with email '{email}' already exists!")
            return
        
        full_name = input("Full Name: ").strip() or "Test User"
        password = input("Password (leave empty for Google-only login): ").strip()
        google_id = input("Google ID (optional): ").strip() or None
        phone = input("Phone: ").strip() or None
        
        # Create user
        user = User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            phone=phone
        )
        
        if password:
            user.password_hash = generate_password_hash(password)
        
        # Optional: Add professional details
        add_details = input("\nAdd professional details? (y/n): ").strip().lower()
        
        if add_details == 'y':
            user.medical_registration_no = input("Medical Registration No: ").strip() or None
            
            print("\nSelect Role:")
            print("1. Doctor")
            print("2. Radiologist")
            role_choice = input("Choice (1-2): ").strip()
            user.specialization = "Doctor" if role_choice == "1" else "Radiologist"
            
            years = input("Years of Experience: ").strip()
            user.years_of_experience = int(years) if years else None
            
            user.hospital = input("Hospital Name: ").strip() or None
            user.hospital_id = input("Hospital ID: ").strip() or None
            user.department = input("Department: ").strip() or None
            
            complete = input("Mark onboarding as complete? (y/n): ").strip().lower()
            user.onboarding_completed = (complete == 'y')
        
        db.session.add(user)
        db.session.commit()
        
        print(f"\n✓ User '{email}' has been added successfully!")
        print(f"   User ID: {user.id}")


def update_user():
    """Update user details"""
    print_header("UPDATE USER")
    email = input("\nEnter email of user to update: ").strip()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"\n❌ No user found with email: {email}")
            return
        
        print(f"\nUpdating user: {user.full_name or user.email}")
        print("(Press Enter to keep current value)\n")
        
        # Update fields
        new_name = input(f"Full Name [{user.full_name}]: ").strip()
        if new_name:
            user.full_name = new_name
        
        new_phone = input(f"Phone [{user.phone}]: ").strip()
        if new_phone:
            user.phone = new_phone
        
        new_med_reg = input(f"Medical Reg No [{user.medical_registration_no}]: ").strip()
        if new_med_reg:
            user.medical_registration_no = new_med_reg
        
        print("\nSelect Role:")
        print("1. Doctor")
        print("2. Radiologist")
        print(f"Current: {user.specialization}")
        role_choice = input("Choice (1-2, or Enter to skip): ").strip()
        if role_choice == "1":
            user.specialization = "Doctor"
        elif role_choice == "2":
            user.specialization = "Radiologist"
        
        new_years = input(f"Years of Experience [{user.years_of_experience}]: ").strip()
        if new_years:
            user.years_of_experience = int(new_years)
        
        new_hospital = input(f"Hospital [{user.hospital}]: ").strip()
        if new_hospital:
            user.hospital = new_hospital
        
        new_dept = input(f"Department [{user.department}]: ").strip()
        if new_dept:
            user.department = new_dept
        
        onboarding = input(f"Onboarding Complete? (y/n) [{'y' if user.onboarding_completed else 'n'}]: ").strip().lower()
        if onboarding:
            user.onboarding_completed = (onboarding == 'y')
        
        db.session.commit()
        print(f"\n✓ User '{email}' has been updated successfully!")


def reset_onboarding():
    """Reset onboarding status for a user"""
    print_header("RESET ONBOARDING")
    email = input("\nEnter email of user: ").strip()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"\n❌ No user found with email: {email}")
            return
        
        user.onboarding_completed = False
        db.session.commit()
        print(f"\n✓ Onboarding reset for '{email}'. User will be redirected to onboarding on next login.")


def show_statistics():
    """Show database statistics"""
    print_header("DATABASE STATISTICS")
    
    with app.app_context():
        total = User.query.count()
        completed = User.query.filter_by(onboarding_completed=True).count()
        incomplete = total - completed
        google_users = User.query.filter(User.google_id.isnot(None)).count()
        doctors = User.query.filter_by(specialization='Doctor').count()
        radiologists = User.query.filter_by(specialization='Radiologist').count()
        
        print(f"\nTotal Users: {total}")
        print(f"Onboarding Complete: {completed}")
        print(f"Onboarding Incomplete: {incomplete}")
        print(f"Google Sign-In Users: {google_users}")
        print(f"Doctors: {doctors}")
        print(f"Radiologists: {radiologists}")


def main_menu():
    """Display main menu and handle user input"""
    while True:
        print_header("NEUROSIGHT DATABASE MANAGER")
        print("\n1.  List All Users")
        print("2.  Search User by Email")
        print("3.  Add Test User")
        print("4.  Update User")
        print("5.  Delete User by Email")
        print("6.  Bulk Delete by IDs")
        print("7.  Delete All Users")
        print("8.  Reset User Onboarding")
        print("9.  Show Statistics")
        print("10. Exit")
        
        choice = input("\nEnter your choice (1-10): ").strip()
        
        if choice == '1':
            list_all_users()
        elif choice == '2':
            search_user()
        elif choice == '3':
            add_test_user()
        elif choice == '4':
            update_user()
        elif choice == '5':
            delete_user()
        elif choice == '6':
            delete_users_by_ids()
        elif choice == '7':
            delete_all_users()
        elif choice == '8':
            reset_onboarding()
        elif choice == '9':
            show_statistics()
        elif choice == '10':
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
