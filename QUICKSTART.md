# 🚀 Quick Start Guide

Get your Vocab Lab running in 5 minutes!

## Step 1: Install Dependencies

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure Environment

```powershell
# Copy environment template
cp .env.example .env

# Generate secure secret key
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# Generate admin password
python generate_password.py
# Copy the output ADMIN_PASSWORD=... line to .env
```

## Step 3: Add API Keys

Edit `.env` and add:

1. **OpenAI API Key**
   - Get from: https://platform.openai.com/api-keys
   - Add to `.env`: `OPENAI_API_KEY=sk-...`

2. **Google Cloud Credentials**
   - Create project at: https://console.cloud.google.com
   - Enable: Vision API + Speech-to-Text API
   - Create service account and download JSON
   - Add to `.env`: `GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json`

## Step 4: Initialize Database

```powershell
python init_db.py
```

## Step 5: Run the Application

```powershell
# Development mode
python app_fixed.py

# Or use setup script for guided setup
python setup.py
```

## Step 6: Access the Application

- **Main app**: http://localhost:5000
- **Admin login**: http://localhost:5000/admin/login
- **Health check**: http://localhost:5000/health

Default admin credentials:
- Username: `admin`
- Password: (what you set in Step 2)

## ✅ Verify Everything Works

1. **Homepage** - Should load with search interface
2. **Search** - Try searching for "你好" or "hello"
3. **Admin Login** - Login with your credentials
4. **Upload Photo** - Test OCR with a Chinese vocabulary photo
5. **Quiz** - Try the quiz feature
6. **Speech** - Test pronunciation recognition

## 🐛 Troubleshooting

**"Module not found" errors**
```powershell
pip install -r requirements.txt
```

**"Database not found" errors**
```powershell
python init_db.py
```

**"OPENAI_API_KEY not set"**
```powershell
# Check .env file has:
OPENAI_API_KEY=sk-...
```

**"Google credentials not found"**
```powershell
# Check .env file has correct path:
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\credentials.json
# File must exist at that path
```

**Admin login doesn't work**
```powershell
# Regenerate password hash:
python generate_password.py
# Copy output to .env
# Restart application
```

## 📚 Next Steps

- Read [README.md](README.md) for full documentation
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Check [PRODUCTION_READY.md](PRODUCTION_READY.md) for what changed

## 🆘 Still Having Issues?

1. Check logs in `logs/` directory
2. Verify all environment variables are set correctly
3. Ensure Python 3.11+ is installed
4. Make sure virtual environment is activated

---

Happy learning! 🎉
