#!/bin/bash
# Cloud Run instance to run backfill_japanese.py on production database
# Usage: gcloud cloud-shell ssh --command=". ./backfill_japanese_cloudshell.sh"

PROJECT_ID="chinese-website-482900"
SERVICE_NAME="chinese"
REGION="europe-west1"

echo "=== Backfill Japanese Translations on Production ==="
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Get the service details
echo "Fetching Cloud Run service details..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
echo "Service URL: $SERVICE_URL"
echo ""

# Authenticate if needed
gcloud auth configure-docker

# Get the latest image deployed
echo "Retrieving deployed image..."
IMAGE=$(gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format='value(spec.template.spec.containers[0].image)')
echo "Image: $IMAGE"
echo ""

# Create a temporary Cloud Run job to execute backfill
echo "Creating temporary Cloud Run job for backfill..."

gcloud run jobs create backfill-japanese-temp-$(date +%s) \
  --image=$IMAGE \
  --region=$REGION \
  --project=$PROJECT_ID \
  --command=python \
  --args=backfill_japanese.py,--only-approved,--limit,1000 \
  --set-env-vars="DATABASE_URL=$(gcloud secrets versions access latest --secret=DATABASE_URL --project=$PROJECT_ID 2>/dev/null || echo 'SET_MANUALLY')" \
  --set-env-vars="OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=OPENAI_API_KEY --project=$PROJECT_ID 2>/dev/null || echo 'SET_MANUALLY')" \
  --wait

echo ""
echo "Backfill complete!"
