#!/bin/bash

# Deploy Japanese translation migration job to Google Cloud Run
# Usage: ./deploy_migration.sh

set -e  # Exit on error

PROJECT_ID="chinese-website-482900"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/migrate-japanese"
JOB_NAME="migrate-japanese"

echo "=========================================="
echo "Deploying Japanese Migration to Google Cloud"
echo "=========================================="

# Step 1: Build Docker image
echo ""
echo "Step 1: Building Docker image..."
docker build -f Dockerfile.migration -t "${IMAGE_NAME}:latest" .

if [ $? -eq 0 ]; then
    echo "[+] Docker image built successfully"
else
    echo "[-] Failed to build Docker image"
    exit 1
fi

# Step 2: Push to Google Container Registry
echo ""
echo "Step 2: Pushing to Google Container Registry..."
docker push "${IMAGE_NAME}:latest"

if [ $? -eq 0 ]; then
    echo "[+] Image pushed successfully"
else
    echo "[-] Failed to push image"
    exit 1
fi

# Step 3: Create Cloud Run Job
echo ""
echo "Step 3: Creating Cloud Run Job..."

# Check if job already exists
if gcloud run jobs describe ${JOB_NAME} --region=${REGION} --project=${PROJECT_ID} 2>/dev/null; then
    echo "Job exists, updating..."
    gcloud run jobs update ${JOB_NAME} \
        --image=${IMAGE_NAME}:latest \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --set-secrets OPENAI_API_KEY=openai-api-key:latest \
        --update-env-vars DATABASE_URL=$(gcloud secrets versions access latest --secret="database-url" --project=${PROJECT_ID})
else
    echo "Creating new job..."
    gcloud run jobs create ${JOB_NAME} \
        --image=${IMAGE_NAME}:latest \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --set-secrets OPENAI_API_KEY=openai-api-key:latest \
        --set-env-vars DATABASE_URL=$(gcloud secrets versions access latest --secret="database-url" --project=${PROJECT_ID})
fi

if [ $? -eq 0 ]; then
    echo "[+] Cloud Run Job created/updated successfully"
else
    echo "[-] Failed to create/update job"
    exit 1
fi

# Step 4: Show job details
echo ""
echo "=========================================="
echo "Job deployment complete!"
echo "=========================================="
echo ""
echo "To run the migration job, execute:"
echo "  gcloud run jobs execute ${JOB_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo ""
echo "To view logs:"
echo "  gcloud run jobs describe ${JOB_NAME} --region=${REGION} --project=${PROJECT_ID}"
echo "  gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}\" --limit=100"
echo ""
