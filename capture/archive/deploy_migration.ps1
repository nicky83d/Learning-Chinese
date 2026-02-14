# Deploy Japanese translation migration job to Google Cloud Run
# Usage: .\deploy_migration.ps1

$PROJECT_ID = "chinese-website-482900"
$REGION = "europe-west1"
$IMAGE_NAME = "gcr.io/${PROJECT_ID}/migrate-japanese"
$JOB_NAME = "migrate-japanese"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deploying Japanese Migration to Google Cloud" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Step 1: Check if gcloud is configured
Write-Host ""
Write-Host "Step 0: Verifying gcloud configuration..." -ForegroundColor Cyan

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[-] gcloud CLI not found. Please install Google Cloud SDK" -ForegroundColor Red
    exit 1
}

$currentProject = gcloud config get-value project 2>$null
if ($currentProject -ne $PROJECT_ID) {
    Write-Host "Setting gcloud project to ${PROJECT_ID}..."
    gcloud config set project $PROJECT_ID
}
Write-Host "[+] gcloud configured" -ForegroundColor Green

# Step 1: Build Docker image
Write-Host ""
Write-Host "Step 1: Building Docker image..." -ForegroundColor Cyan

docker build -f Dockerfile.migration -t "${IMAGE_NAME}:latest" .

if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Docker image built successfully" -ForegroundColor Green
} else {
    Write-Host "[-] Failed to build Docker image" -ForegroundColor Red
    exit 1
}

# Step 2: Configure Docker for GCR
Write-Host ""
Write-Host "Step 2: Configuring Docker for Google Container Registry..." -ForegroundColor Cyan

# This requires gcloud auth configure-docker to be run first
gcloud auth configure-docker gcr.io

# Step 3: Push to Google Container Registry
Write-Host ""
Write-Host "Step 3: Pushing to Google Container Registry..." -ForegroundColor Cyan

docker push "${IMAGE_NAME}:latest"

if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Image pushed successfully" -ForegroundColor Green
} else {
    Write-Host "[-] Failed to push image" -ForegroundColor Red
    exit 1
}

# Step 4: Get DATABASE_URL from secrets
Write-Host ""
Write-Host "Step 4: Retrieving secrets from Google Secret Manager..." -ForegroundColor Cyan

$databaseUrl = gcloud secrets versions access latest --secret="database-url" --project=$PROJECT_ID 2>$null

if (-not $databaseUrl) {
    Write-Host "[-] Could not retrieve DATABASE_URL secret. Please ensure 'database-url' secret exists." -ForegroundColor Red
    Write-Host "    Create it with: gcloud secrets create database-url --data-file=- " -ForegroundColor Yellow
    exit 1
}

Write-Host "[+] Secrets retrieved" -ForegroundColor Green

# Step 5: Create or update Cloud Run Job
Write-Host ""
Write-Host "Step 5: Creating/Updating Cloud Run Job..." -ForegroundColor Cyan

# Check if job already exists
$jobExists = gcloud run jobs describe $JOB_NAME --region=$REGION --project=$PROJECT_ID 2>$null

if ($jobExists) {
    Write-Host "Job exists, updating..."
    gcloud run jobs update $JOB_NAME `
        --image="${IMAGE_NAME}:latest" `
        --region=$REGION `
        --project=$PROJECT_ID `
        --set-secrets OPENAI_API_KEY=openai-api-key:latest `
        --update-env-vars DATABASE_URL=$databaseUrl
} else {
    Write-Host "Creating new job..."
    gcloud run jobs create $JOB_NAME `
        --image="${IMAGE_NAME}:latest" `
        --region=$REGION `
        --project=$PROJECT_ID `
        --set-secrets OPENAI_API_KEY=openai-api-key:latest `
        --set-env-vars DATABASE_URL=$databaseUrl
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Cloud Run Job created/updated successfully" -ForegroundColor Green
} else {
    Write-Host "[-] Failed to create/update job" -ForegroundColor Red
    exit 1
}

# Step 6: Show completion message
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Job deployment complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the migration job, execute:" -ForegroundColor Yellow
Write-Host "  gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT_ID" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view execution logs:" -ForegroundColor Yellow
Write-Host "  gcloud run jobs describe $JOB_NAME --region=$REGION --project=$PROJECT_ID" -ForegroundColor Cyan
Write-Host "  gcloud logging read `"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME`" --limit=100" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Secrets must exist in Google Secret Manager:" -ForegroundColor Yellow
Write-Host "  - openai-api-key: Your OpenAI API key" -ForegroundColor Cyan
Write-Host "  - database-url: Your PostgreSQL connection string" -ForegroundColor Cyan
Write-Host ""
