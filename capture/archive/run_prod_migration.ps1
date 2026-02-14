# Run migration on Cloud Run production database
# Usage: .\run_prod_migration.ps1

Write-Host "🚀 Running migration on Cloud Run..." -ForegroundColor Cyan

# Step 1: Deploy the latest code (includes migration script)
Write-Host "`n📦 Deploying latest code to Cloud Run..." -ForegroundColor Yellow
git add .
git commit -m "Add PhotoLog migration support" -ErrorAction SilentlyContinue
git push origin main

Write-Host "`n⏳ Waiting for deployment to complete (60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Step 2: Run migration via Cloud Run Jobs
Write-Host "`n🔧 Executing migration job on Cloud Run..." -ForegroundColor Yellow
gcloud run jobs create migrate-photo-log-temp `
  --image=gcr.io/chinese-website-482900/chinese:latest `
  --region=europe-west1 `
  --project=chinese-website-482900 `
  --add-cloudsql-instances=chinese-website-482900:europe-west1:chinese-db `
  --set-env-vars="DATABASE_URL=postgresql+pg8000://postgres:mgB95PsgUxtAkgCL2lLvpbFNvVrih9W@/vocab?unix_sock=/cloudsql/chinese-website-482900:europe-west1:chinese-db/.s.PGSQL.5432" `
  --command="python" `
  --args="migrate_photo_log_updates.py" `
  --execute-now `
  --wait

Write-Host "`n✅ Migration complete! Cleaning up job..." -ForegroundColor Green
gcloud run jobs delete migrate-photo-log-temp --region=europe-west1 --project=chinese-website-482900 --quiet

Write-Host "`n🎉 All done! Refresh your admin panel." -ForegroundColor Green
