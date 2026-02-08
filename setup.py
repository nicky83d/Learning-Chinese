#!/usr/bin/env python3
"""
Quick setup script for Vocab Lab
Checks dependencies and helps with initial configuration
"""
import os
import sys
import subprocess
import secrets

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_venv():
    """Check if virtual environment is active"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment active")
        return True
    print("⚠️  No virtual environment detected")
    print("   Recommended: python -m venv .venv && .venv\\Scripts\\activate (Windows)")
    return False

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if os.path.exists('.env'):
        print("✅ .env file exists")
        return True
    
    if not os.path.exists('.env.example'):
        print("❌ .env.example not found")
        return False
    
    print("\n📝 Creating .env file...")
    with open('.env.example', 'r') as example:
        content = example.read()
    
    # Generate a random SECRET_KEY
    secret_key = secrets.token_hex(32)
    content = content.replace('your-secret-key-here-change-in-production', secret_key)
    
    with open('.env', 'w') as env_file:
        env_file.write(content)
    
    print("✅ .env file created with random SECRET_KEY")
    print("⚠️  Please edit .env and add your API keys:")
    print("   - OPENAI_API_KEY")
    print("   - GOOGLE_APPLICATION_CREDENTIALS")
    print("   - ADMIN_PASSWORD (use bcrypt hash)")
    return True

def check_env_vars():
    """Check if required environment variables are set"""
    print("\n🔍 Checking environment configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required = {
        'OPENAI_API_KEY': 'OpenAI API key',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Google Cloud credentials path',
        'ADMIN_PASSWORD': 'Admin password'
    }
    
    missing = []
    for var, description in required.items():
        if not os.getenv(var):
            missing.append(f"   - {var} ({description})")
            print(f"❌ {var} not set")
        else:
            print(f"✅ {var} configured")
    
    if missing:
        print("\n⚠️  Missing required variables in .env:")
        for item in missing:
            print(item)
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    dirs = ['uploads', 'logs', 'instance']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ {dir_name}/ created")
    return True

def init_database():
    """Initialize database"""
    print("\n🗄️  Initializing database...")
    try:
        subprocess.check_call([sys.executable, "init_db.py"])
        print("✅ Database initialized")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to initialize database")
        return False

def generate_admin_password():
    """Helper to generate bcrypt password"""
    print("\n🔐 Generate admin password hash:")
    password = input("Enter admin password (or press Enter to skip): ").strip()
    
    if not password:
        print("Skipped")
        return
    
    try:
        import bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        print(f"\n✅ Bcrypt hash generated:")
        print(f"   {hashed.decode()}")
        print("\n   Add this to your .env file:")
        print(f"   ADMIN_PASSWORD={hashed.decode()}")
    except ImportError:
        print("❌ bcrypt not installed")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Vocab Lab - Setup Script")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check virtual environment
    check_venv()
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create .env file
    if not create_env_file():
        return 1
    
    # Check environment variables
    env_configured = check_env_vars()
    
    # Create directories
    create_directories()
    
    # Generate admin password if needed
    if not env_configured:
        generate_admin_password()
    
    # Initialize database if env is configured
    if env_configured:
        init_database()
    
    print("\n" + "=" * 60)
    if env_configured:
        print("✅ Setup complete!")
        print("\nNext steps:")
        print("   1. Review .env file")
        print("   2. Run: python app_fixed.py")
        print("   3. Visit: http://localhost:5000")
        print("   4. Admin: http://localhost:5000/admin/login")
    else:
        print("⚠️  Setup incomplete")
        print("\nNext steps:")
        print("   1. Edit .env and add your API keys")
        print("   2. Run this script again to initialize database")
        print("\nFor help, see README.md or DEPLOYMENT.md")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
