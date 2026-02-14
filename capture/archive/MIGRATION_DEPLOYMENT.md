# Google Cloud Production Migration Deployment Guide

## Overview

This guide walks you through deploying the Japanese translation migration to Google Cloud Run, where it will connect to your production PostgreSQL database and translate all vocabulary items using OpenAI's API.

## Architecture

- **Compute**: Google Cloud Run (Job)
- **Database**: Cloud SQL (PostgreSQL)
- **Secrets**: Google Secret Manager
- **Docker Image Registry**: Google Container Registry (GCR)

## Prerequisites

1. **Google Cloud SDK installed**
   - Download: https://cloud.google.com/sdk/docs/install
   - Verify: `gcloud --version`

2. **Docker installed**
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version`

3. **Project Access**
   - Project ID: `chinese-website-482900`
   - Region: `europe-west1`

4. **API Keys**
   - OpenAI API key (from https://platform.openai.com/api-keys)
   - PostgreSQL connection string (from Google Cloud SQL instance)

## Step-by-Step Deployment

### Step 1: Setup Secrets in Google Secret Manager

This stores your sensitive credentials securely.

```powershell
# Windows PowerShell:
.\setup_secrets.ps1
```

This script will:
1. Prompt you for your OpenAI API key
2. Prompt you for your PostgreSQL connection string
3. Create/update secrets in Google Secret Manager

**What you'll need:**

- **OPENAI_API_KEY**: Get from https://platform.openai.com/api-keys
- **DATABASE_URL**: Get from your Cloud SQL instance
  - Format: `postgresql://username:password@cloudsql-ip:5432/database?sslmode=require`
  - To find it: Google Cloud Console → SQL instances → [Your instance] → Connection name

### Step 2: Authentication with Google Cloud

```powershell
# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project chinese-website-482900

# Configure Docker for GCR
gcloud auth configure-docker gcr.io
```

### Step 3: Deploy the Migration Job

```powershell
# Windows PowerShell:
.\deploy_migration.ps1
```

This script will:
1. Build a Docker image with the migration code
2. Push it to Google Container Registry
3. Create a Cloud Run Job with the image
4. Configure environment variables and secrets

**Expected output:**
```
==========================================
Deploying Japanese Migration to Google Cloud
==========================================
...
[+] Docker image built successfully
[+] Image pushed successfully
[+] Cloud Run Job created/updated successfully
==========================================
Job deployment complete!
==========================================

To run the migration job, execute:
  gcloud run jobs execute migrate-japanese --region=europe-west1 --project=chinese-website-482900
```

### Step 4: Execute the Migration

Once deployment is complete, run the migration:

```powershell
# Execute the migration job
gcloud run jobs execute migrate-japanese `
  --region=europe-west1 `
  --project=chinese-website-482900

# Wait a moment, then check status
gcloud run jobs describe migrate-japanese `
  --region=europe-west1 `
  --project=chinese-website-482900
```

### Step 5: Monitor Progress

View logs in real-time:

```powershell
# Get recent logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=migrate-japanese" `
  --limit=100 `
  --project=chinese-website-482900

# Or use Cloud Logging in Google Cloud Console
# Navigate to: Cloud Logging → Logs Explorer
# Filter: resource.type="cloud_run_job" AND resource.labels.job_name="migrate-japanese"
```

## What the Migration Does

1. **Connects to Production Database**
   - Uses the DATABASE_URL secret to connect to Cloud SQL PostgreSQL

2. **Finds Vocabulary Items**
   - Queries for all items with empty or NULL `japanese_kanji` or `japanese_romaji` columns

3. **Translates with OpenAI**
   - For each word: Calls GPT-3.5-turbo to translate Chinese hanzi to Japanese kanji + romaji
   - For each sentence: Calls GPT-3.5-turbo to translate example sentences
   - Handles rate limits (waits 60 seconds if hit)

4. **Updates Database**
   - Populates `japanese_kanji`, `japanese_romaji`, `sent_japanese_kanji`, `sent_japanese_romaji`
   - Commits every 10 items for safety

5. **Logs Progress**
   - All translations are logged to Google Cloud Logging
   - Visible in Cloud Console or via `gcloud logging read`

## Expected Timeline

- **Estimated items to translate**: ~300-400
- **Time per item**: ~3-5 seconds (with OpenAI API latency)
- **Total time**: 30-90 minutes (depending on rate limiting)

## Troubleshooting

### Build fails: "no such file or directory"
- Ensure you're in the correct directory (the project root with Dockerfile.migration)
- Run: `cd C:\Users\nicod\OneDrive\Desktop\Chinese\website`

### Docker push fails: "unauthorized"
- Re-run: `gcloud auth configure-docker gcr.io`
- Verify you're logged in with: `gcloud auth list`

### Job fails with "Secret not found"
- Verify secrets exist: `gcloud secrets list --project=chinese-website-482900`
- Run `setup_secrets.ps1` again to create missing secrets
- Check secret values: `gcloud secrets versions access latest --secret=openai-api-key`

### Job fails with "DATABASE_URL": 
- Verify the PostgreSQL connection string is correct
- Test locally first with: `psql <your-connection-string>`
- Ensure Cloud SQL Proxy isn't needed (check your network setup)

### Migration is slow / getting rate limited
- This is normal - OpenAI has rate limits
- The script waits 60 seconds on rate limit errors
- With free tier, expect 20-30 minutes for 300+ items

### Need to cancel/stop the job
```powershell
# Jobs in GCP run to completion or failure
# If you need to stop it:
# 1. Wait for it to complete
# 2. Or delete the job and create a new one:
gcloud run jobs delete migrate-japanese --region=europe-west1 --project=chinese-website-482900
```

## After Migration Completes

Once the migration finishes successfully:

1. **Verify in Database**
   ```sql
   SELECT COUNT(*) FROM vocabulary WHERE japanese_kanji != '' AND japanese_kanji IS NOT NULL;
   ```

2. **Check Frontend**
   - Visit https://chinese-9759877084774.europe-west1.run.app
   - You should now see Japanese (kanji) and romaji alongside Chinese and Pinyin

3. **Optional: Delete Job**
   - If you don't need to run migration again:
   ```powershell
   gcloud run jobs delete migrate-japanese --region=europe-west1 --project=chinese-website-482900
   ```

## Migration Script Details

**File**: `migrate_production.py`

**Key Features**:
- Connects to PostgreSQL via SQLAlchemy
- Translates using OpenAI GPT-3.5-turbo
- Handles rate limiting with exponential backoff
- Commits every 10 items for robustness
- Detailed logging to Google Cloud Logging
- Error handling and retry logic

**Source Code**: See `migrate_production.py` in the project root

## Support

For issues or questions:
1. Check logs: `gcloud logging read "resource.type=cloud_run_job"`
2. Review the deployment output
3. Verify secrets are set correctly
4. Test locally with `migrate_japanese_simple.py` first

---

**Project**: Chinese Vocabulary Learning Platform  
**Version**: 2.0 (with Japanese support)  
**Last Updated**: February 2026
