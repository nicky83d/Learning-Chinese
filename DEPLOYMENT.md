# 🚀 Production Deployment Guide - Vocab Lab

## Overview
This guide covers deploying the Chinese Vocabulary Learning Platform to production. The application is a Flask-based web app with Google Cloud Vision OCR, OpenAI GPT, and Google Speech-to-Text integrations.

## 📋 Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Python 3.11+ installed
- [ ] Google Cloud project created with Vision API and Speech-to-Text API enabled
- [ ] OpenAI API account with GPT-4o-mini access
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (required for production)

### 2. Required Services
- [ ] Web server (Heroku, AWS, Google Cloud Run, or DigitalOcean)
- [ ] PostgreSQL database (recommended) or SQLite for small deployments
- [ ] Redis instance (optional, for rate limiting)

## 🔧 Configuration

### Step 1: Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required variables:**
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-a-strong-random-key>

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# API Keys
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Admin Credentials (use bcrypt-hashed password)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<bcrypt-hashed-password>

# Optional: Rate Limiting
REDIS_URL=redis://localhost:6379/0

# Optional: CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Step 2: Generate Secure Passwords

**Generate SECRET_KEY:**
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Generate bcrypt-hashed admin password:**
```python
python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

### Step 3: Google Cloud Service Account
1. Create service account in Google Cloud Console
2. Enable Vision API and Speech-to-Text API
3. Download JSON key file
4. Set `GOOGLE_APPLICATION_CREDENTIALS` to the file path

## 🚢 Deployment Options

### Option 1: Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis (optional)
heroku addons:create heroku-redis:mini

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=<your-secret-key>
heroku config:set OPENAI_API_KEY=<your-api-key>
heroku config:set ADMIN_USERNAME=admin
heroku config:set ADMIN_PASSWORD=<bcrypt-hash>

# Upload Google credentials
# Method 1: Use environment variable for JSON content
heroku config:set GOOGLE_CREDENTIALS="$(cat path/to/credentials.json)"

# Deploy
git push heroku main

# Run database migrations
heroku run python init_db.py
```

### Option 2: Google Cloud Run

```bash
# Build and deploy
gcloud run deploy vocab-lab \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production,SECRET_KEY=<key> \
  --set-secrets OPENAI_API_KEY=openai-key:latest,ADMIN_PASSWORD=admin-pass:latest
```

### Option 3: DigitalOcean App Platform

1. Connect GitHub repository
2. Set environment variables in dashboard
3. Configure build command: `pip install -r requirements.txt`
4. Configure run command: `gunicorn app_fixed:app`
5. Deploy

### Option 4: AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 vocab-lab

# Create environment
eb create vocab-lab-prod --envvars FLASK_ENV=production,SECRET_KEY=<key>,...

# Deploy
eb deploy
```

### Option 5: Traditional VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip nginx postgresql redis-server

# Setup application
cd /var/www/vocab-lab
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Setup systemd service
sudo cp deploy/vocab-lab.service /etc/systemd/system/
sudo systemctl enable vocab-lab
sudo systemctl start vocab-lab

# Configure Nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/vocab-lab
sudo ln -s /etc/nginx/sites-available/vocab-lab /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## 🗄️ Database Setup

### PostgreSQL (Recommended)
```bash
# Create database
createdb vocab_lab

# Update DATABASE_URL
export DATABASE_URL=postgresql://user:password@localhost/vocab_lab

# Initialize
python init_db.py
```

### SQLite (Development/Small Deployments)
```bash
# Will be created automatically
python init_db.py
```

## 🔒 Security Hardening

### 1. HTTPS/SSL
- **Required for production**
- Use Let's Encrypt for free SSL certificates
- Configure `SESSION_COOKIE_SECURE=True` in production config

### 2. Firewall Rules
```bash
# Allow only HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Rate Limiting
- Redis is recommended for distributed rate limiting
- In-memory rate limiting works for single-server deployments

### 4. Admin Access
- Change default admin username
- Use strong, bcrypt-hashed passwords
- Consider adding IP whitelist for admin panel
- Enable session timeout (default: 24 hours)

### 5. API Key Protection
- **Never** commit `.env` file
- Use secret management systems (AWS Secrets Manager, Google Secret Manager, etc.)
- Rotate keys regularly

## 📊 Monitoring & Logging

### Application Logs
Logs are written to `logs/photo_processing_YYYYMMDD.log`

### Production Logging
Configure external logging service:
- **Papertrail**: Simple log aggregation
- **Loggly**: Advanced log analysis
- **CloudWatch** (AWS): Native AWS integration
- **Cloud Logging** (GCP): Native GCP integration

### Health Check Endpoint
Add to `app_fixed.py`:
```python
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
```

### Monitoring Services
- **UptimeRobot**: Free uptime monitoring
- **Pingdom**: Advanced monitoring
- **New Relic**: APM and performance monitoring

## 🔄 Database Migrations

### Initial Setup
```bash
python init_db.py
```

### Future Migrations
Use Flask-Migrate (optional):
```bash
pip install Flask-Migrate
flask db init
flask db migrate -m "Description"
flask db upgrade
```

## 📦 Static Files & CDN

### Option 1: Serve from Application
Default - static files served by Flask/Gunicorn

### Option 2: CDN (Recommended for Production)
1. Upload static files to CDN (CloudFront, Cloudflare, etc.)
2. Update `STATIC_URL` in config
3. Configure CORS headers

## 🚨 Troubleshooting

### Common Issues

**1. Database connection errors**
```bash
# Check DATABASE_URL format
# PostgreSQL: postgresql://user:pass@host:port/db
# Ensure database exists and credentials are correct
```

**2. Google Vision API errors**
```bash
# Verify GOOGLE_APPLICATION_CREDENTIALS path
# Ensure Vision API is enabled in GCP console
# Check service account has necessary permissions
```

**3. OpenAI API errors**
```bash
# Verify OPENAI_API_KEY is set correctly
# Check API quota and billing status
# Review rate limits
```

**4. Session/Authentication issues**
```bash
# Ensure SECRET_KEY is set in production
# Check SESSION_COOKIE_SECURE matches HTTPS status
# Verify bcrypt password hash format
```

**5. File upload errors**
```bash
# Ensure uploads/ directory exists and is writable
# Check MAX_CONTENT_LENGTH setting (default: 16MB)
# Verify disk space availability
```

## 🧪 Testing Production Configuration

### Local Production Test
```bash
# Set production environment
export FLASK_ENV=production
export SECRET_KEY=test-key
export ADMIN_PASSWORD=$(python -c "import bcrypt; print(bcrypt.hashpw(b'test123', bcrypt.gensalt()).decode())")

# Run with Gunicorn
gunicorn app_fixed:app --bind 0.0.0.0:8000 --workers 2

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/admin/login
```

## 📱 Mobile Optimization

The application is responsive but consider:
- Testing on various devices
- Optimizing image uploads on mobile
- Checking camera access permissions
- Testing speech recognition on mobile browsers

## 🔄 Backup Strategy

### Database Backups
```bash
# PostgreSQL
pg_dump vocab_lab > backup_$(date +%Y%m%d).sql

# Automate with cron
0 2 * * * pg_dump vocab_lab > /backups/vocab_lab_$(date +\%Y\%m\%d).sql
```

### Upload Files
```bash
# Sync to S3
aws s3 sync uploads/ s3://your-bucket/uploads/

# Or use rsync for another server
rsync -avz uploads/ user@backup-server:/backups/uploads/
```

## 🚀 Performance Optimization

### 1. Database Indexing
Ensure indexes on frequently queried fields (done in models.py)

### 2. Caching
Consider adding Flask-Caching:
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

### 3. Gunicorn Configuration
```bash
# Adjust workers based on CPU cores
workers = (2 * CPU_cores) + 1

# Increase timeout for photo processing
--timeout 120
```

### 4. CDN for Static Assets
Use CloudFlare, AWS CloudFront, or similar

## 📄 License & Compliance

- Ensure OpenAI API usage complies with their terms
- Review Google Cloud API terms
- Add privacy policy for user data (IP addresses, uploaded photos)
- Consider GDPR compliance if serving EU users

## 🆘 Support & Maintenance

### Regular Maintenance Tasks
- [ ] Monitor API usage and costs
- [ ] Review and clean up old photo logs
- [ ] Update dependencies monthly
- [ ] Review logs for errors
- [ ] Test backup restoration
- [ ] Monitor disk space

### Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Test in staging environment first
# Deploy to production after testing
```

## 📚 Additional Resources

- [Flask Production Deployment](https://flask.palletsprojects.com/en/latest/deploying/)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

## ✅ Final Checklist Before Going Live

- [ ] All environment variables set correctly
- [ ] SECRET_KEY is strong and unique
- [ ] Admin password is bcrypt-hashed
- [ ] HTTPS/SSL configured
- [ ] Database initialized and backed up
- [ ] Rate limiting enabled
- [ ] Logs configured and monitored
- [ ] Health check endpoint working
- [ ] Error pages customized (404, 500)
- [ ] Privacy policy added
- [ ] Terms of service added (if needed)
- [ ] Test all features end-to-end
- [ ] Load testing completed
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Domain DNS configured
- [ ] CDN configured (optional)
- [ ] Mobile testing completed

**Once deployed, test these critical paths:**
1. Homepage loads
2. Search functionality works
3. Admin login works
4. Photo upload and OCR processing works
5. Quiz functionality works
6. Speech recognition works
7. Admin can approve/reject/delete uploads

---

🎉 **Your Vocab Lab is now production-ready!** For questions or issues, refer to the application logs and monitoring dashboards.
