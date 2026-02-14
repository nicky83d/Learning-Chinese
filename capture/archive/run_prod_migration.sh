#!/bin/bash
# Run migration on Cloud Run production database
# Usage: ./run_prod_migration.sh

echo "🚀 Running migration on Cloud Run..."

gcloud run jobs create migrate-photo-log \
  --image=gcr.io/chinese-website-482900/chinese \
  --region=europe-west1 \
  --project=chinese-website-482900 \
  --add-cloudsql-instances=chinese-website-482900:europe-west1:chinese-db \
  --set-env-vars="DATABASE_URL=postgresql+pg8000://postgres:mgB95PsgUxtAkgCL2lLvpbFNvVrih9W@/vocab?unix_sock=/cloudsql/chinese-website-482900:europe-west1:chinese-db/.s.PGSQL.5432" \
  --command="python" \
  --args="migrate_photo_log_updates.py" \
  --execute-now \
  --wait

echo "✅ Migration complete!"
