# Cloud Shell Commands - Copy & Paste Ready

## STEP 1: Build Image Without Cache

```bash
# Set your project ID and image name
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="swipe-signals"
REGION="asia-southeast1"

# Build without cache (this ensures latest files are included)
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --no-cache \
  --timeout=2400s

# Save image URI for later
IMAGE_URI="gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"
echo "Image built: $IMAGE_URI"
```

---

## STEP 2: Verify CSV Files Exist in Docker Image

```bash
# Quick check - list all CSV files in image
docker run $IMAGE_URI sh -c "ls -lh /opt/app/*.csv"

# Verify each file has data
docker run $IMAGE_URI sh -c "
echo '=== X_train_final.csv ==='
head -1 /opt/app/X_train_final.csv | tr ',' '\n' | head -5
echo ''
echo '=== dating_app_behavior_dataset.csv ==='
head -1 /opt/app/dating_app_behavior_dataset.csv | tr ',' '\n' | head -5
echo ''
echo '=== Checking row counts ==='
wc -l /opt/app/X_train_final.csv /opt/app/dating_app_behavior_dataset.csv
"
```

---

## STEP 3: Test Python Can Load Files

```bash
# Verify files can be loaded by pandas
docker run $IMAGE_URI python3 << 'EOF'
import pandas as pd
import os

print("=== Checking CSV Files in Container ===\n")

files_to_check = {
    'X_train_final.csv': 'Training features',
    'y_train_final.csv': 'Training labels',
    'X_test_final.csv': 'Test features',
    'y_test_final.csv': 'Test labels',
    'dating_app_behavior_dataset.csv': 'Raw data for thresholds'
}

for fname, description in files_to_check.items():
    path = f'/opt/app/{fname}'
    try:
        df = pd.read_csv(path)
        print(f"✓ {fname}")
        print(f"  └─ {description}: {df.shape}")
    except Exception as e:
        print(f"✗ {fname} - ERROR: {e}")

print("\n=== Checking Deployment Artifacts ===\n")
import joblib
import json

artifacts = [
    ('deployment_artifacts/ordinal_encoder.pkl', 'joblib'),
    ('deployment_artifacts/standard_scaler.pkl', 'joblib'),
    ('deployment_artifacts/feature_columns.json', 'json'),
    ('deployment_artifacts/engagement_mapping.json', 'json'),
]

for fname, ftype in artifacts:
    path = f'/opt/app/{fname}'
    try:
        if ftype == 'joblib':
            obj = joblib.load(path)
            print(f"✓ {fname}")
        else:
            with open(path, 'r') as f:
                obj = json.load(f)
            print(f"✓ {fname}")
    except Exception as e:
        print(f"✗ {fname} - ERROR: {e}")
EOF
```

---

## STEP 4: Deploy to Cloud Run

### Option A: First time deployment or updating service
```bash
gcloud run deploy swipe-signals \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600 \
  --allow-unauthenticated \
  --set-env-vars "PORT=8080"

# Get the service URL
SERVICE_URL=$(gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.url)')

echo "Service deployed at: $SERVICE_URL"
```

### Option B: If service already exists (just update to latest image)
```bash
# This ensures Cloud Run pulls the latest built image
gcloud run deploy swipe-signals \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --no-traffic  # Deploy but don't route traffic yet

# Then route traffic to latest revision
gcloud run services update-traffic swipe-signals \
  --to-revisions LATEST=100 \
  --platform managed \
  --region $REGION
```

---

## STEP 5: Verify Deployment Success

```bash
# Get current service details
gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.url)'

# View deployment logs (last 50 lines)
gcloud run logs read swipe-signals \
  --platform managed \
  --region $REGION \
  --limit 50 \
  --follow

# Test the service is running
SERVICE_URL=$(gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.url)')

curl -s $SERVICE_URL | head -20  # Should return HTML page
```

---

## STEP 6: If You Need to Force Latest Image

### Problem: Cloud Run is using old cached image

### Solution A: Redeploy with explicit `--no-cache` (as done in STEP 1)
```bash
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --no-cache \
  --timeout=2400s

# Then immediately deploy (forces pull of new image)
gcloud run deploy swipe-signals \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --platform managed \
  --region $REGION
```

### Solution B: Use timestamp tag to force new revision
```bash
TIMESTAMP=$(date +%s)
TAG="gcr.io/$PROJECT_ID/$IMAGE_NAME:v$TIMESTAMP"

gcloud builds submit \
  --tag $TAG \
  --no-cache

gcloud run deploy swipe-signals \
  --image $TAG \
  --platform managed \
  --region $REGION
```

### Solution C: Check which revision is running
```bash
# List all revisions
gcloud run revisions list \
  --service swipe-signals \
  --platform managed \
  --region $REGION

# Get detailed info on current revision
gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.latestReadyRevisionName)'
```

---

## STEP 7: Troubleshooting

### If EDA tab shows "files missing"
```bash
# Check app logs
gcloud run logs read swipe-signals \
  --platform managed \
  --region $REGION \
  --limit 100

# The error should tell you which file path failed
```

### If feature colors are all the same
```bash
# Verify dating_app_behavior_dataset.csv is in container
docker run $IMAGE_URI sh -c "
python3 -c \"
import pandas as pd
df = pd.read_csv('/opt/app/dating_app_behavior_dataset.csv')
cols = ['likes_received', 'mutual_matches', 'message_sent_count', 'profile_pics_count', 'bio_length', 'swipe_right_ratio', 'emoji_usage_rate']
print('Column means:')
for col in cols:
    if col in df.columns:
        print(f'  {col}: {df[col].mean():.3f}')
\"
"
```

### If app is running old code
```bash
# Compare current revision image with latest built image
CURRENT_REVISION=$(gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.latestReadyRevisionName)')

gcloud run revisions describe $CURRENT_REVISION \
  --platform managed \
  --region $REGION \
  --format='value(spec.template.spec.containers[0].image)'

# Should match: gcr.io/$PROJECT_ID/$IMAGE_NAME:latest
```

---

## One-Command Quick Deploy (Copy Everything Below)

```bash
#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="swipe-signals"
REGION="asia-southeast1"
IMAGE_URI="gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"

echo "Step 1: Building image without cache..."
gcloud builds submit \
  --tag $IMAGE_URI \
  --no-cache \
  --timeout=2400s

echo -e "\nStep 2: Verifying CSV files in image..."
docker run $IMAGE_URI sh -c "ls -lh /opt/app/*.csv"

echo -e "\nStep 3: Deploying to Cloud Run..."
gcloud run deploy swipe-signals \
  --image $IMAGE_URI \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 1 \
  --allow-unauthenticated

echo -e "\nStep 4: Getting service URL..."
SERVICE_URL=$(gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.url)')

echo -e "\n✓ Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo "Check logs: gcloud run logs read swipe-signals --platform managed --region $REGION --limit 50 --follow"
```

Save the above as `deploy.sh`, then run:
```bash
chmod +x deploy.sh
./deploy.sh
```
