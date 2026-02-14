#!/usr/bin/env python3
"""
Password hash generator for admin authentication
Run this to generate a bcrypt-hashed password for ADMIN_PASSWORD in .env
"""
import sys
import bcrypt
import getpass

def generate_password_hash():
    """Generate bcrypt password hash"""
    print("=" * 60)
    print("🔐 Admin Password Hash Generator")
    print("=" * 60)
    print()
    
    # Get password from user
    while True:
        password = getpass.getpass("Enter admin password: ")
        if not password:
            print("❌ Password cannot be empty")
            continue
        
        if len(password) < 8:
            print("⚠️  Password should be at least 8 characters")
            confirm = input("Continue anyway? (y/N): ").strip().lower()
            if confirm != 'y':
                continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords don't match. Try again.")
            continue
        
        break
    
    # Generate hash
    print("\n⏳ Generating hash...")
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hash_str = hashed.decode('utf-8')
    
    print("\n✅ Password hash generated successfully!")
    print("\n" + "=" * 60)
    print("Add this line to your .env file:")
    print("=" * 60)
    print(f"ADMIN_PASSWORD={hash_str}")
    print("=" * 60)
    print("\n⚠️  Keep this hash secret and never commit it to version control!")
    print()
    
    return hash_str

if __name__ == "__main__":
    try:
        generate_password_hash()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
