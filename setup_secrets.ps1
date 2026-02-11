# Setup secrets in Google Secret Manager for migration job
# This script ensures OPENAI_API_KEY and DATABASE_URL are available

$PROJECT_ID = "chinese-website-482900"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setting up Google Secret Manager" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Check gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[-] gcloud CLI not found. Please install Google Cloud SDK" -ForegroundColor Red
    exit 1
}

Write-Host "Setting project to ${PROJECT_ID}..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# Secret 1: OPENAI_API_KEY
Write-Host ""
Write-Host "Step 1: OPENAI_API_KEY" -ForegroundColor Cyan

$secretExists = gcloud secrets describe openai-api-key --project=$PROJECT_ID 2>$null
if ($secretExists) {
    Write-Host "[*] Secret 'openai-api-key' already exists" -ForegroundColor Yellow
    $response = Read-Host "Update it? (y/n)"
    if ($response -eq 'y') {
        $apiKey = Read-Host "Enter your OpenAI API key" -AsSecureString
        $apiKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($apiKey))
        $apiKeyPlain | gcloud secrets versions add openai-api-key --data-file=- --project=$PROJECT_ID
        Write-Host "[+] Secret updated" -ForegroundColor Green
    } else {
        Write-Host "[*] Keeping existing secret" -ForegroundColor Yellow
    }
} else {
    Write-Host "[-] Secret 'openai-api-key' does not exist" -ForegroundColor Yellow
    Write-Host "Creating it now..." -ForegroundColor Cyan
    $apiKey = Read-Host "Enter your OpenAI API key" -AsSecureString
    $apiKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($apiKey))
    
    # Create the secret
    Write-Host $apiKeyPlain | gcloud secrets create openai-api-key --data-file=- --project=$PROJECT_ID
    Write-Host "[+] Secret 'openai-api-key' created" -ForegroundColor Green
}

# Secret 2: DATABASE_URL (PostgreSQL connection string)
Write-Host ""
Write-Host "Step 2: DATABASE_URL" -ForegroundColor Cyan

$secretExists = gcloud secrets describe database-url --project=$PROJECT_ID 2>$null
if ($secretExists) {
    Write-Host "[*] Secret 'database-url' already exists" -ForegroundColor Yellow
    $response = Read-Host "Update it? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Connection format: postgresql://user:password@host:5432/database?sslmode=require" -ForegroundColor Gray
        $dbUrl = Read-Host "Enter your PostgreSQL connection string" -AsSecureString
        $dbUrlPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($dbUrl))
        Write-Host $dbUrlPlain | gcloud secrets versions add database-url --data-file=- --project=$PROJECT_ID
        Write-Host "[+] Secret updated" -ForegroundColor Green
    } else {
        Write-Host "[*] Keeping existing secret" -ForegroundColor Yellow
    }
} else {
    Write-Host "[-] Secret 'database-url' does not exist" -ForegroundColor Yellow
    Write-Host "You can find your connection string in Google Cloud Console > Cloud SQL" -ForegroundColor Gray
    Write-Host "Format: postgresql://user:password@host:5432/database?sslmode=require" -ForegroundColor Gray
    $dbUrl = Read-Host "Enter your PostgreSQL connection string" -AsSecureString
    $dbUrlPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($dbUrl))
    
    Write-Host $dbUrlPlain | gcloud secrets create database-url --data-file=- --project=$PROJECT_ID
    Write-Host "[+] Secret 'database-url' created" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Secrets setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\deploy_migration.ps1" -ForegroundColor Cyan
Write-Host "2. Then execute: gcloud run jobs execute migrate-japanese --region=europe-west1 --project=chinese-website-482900" -ForegroundColor Cyan
Write-Host ""
