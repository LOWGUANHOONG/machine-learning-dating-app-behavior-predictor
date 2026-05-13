# Cloud Run Deployment Verification Checklist

## Files Required & Their Purpose

### 1. **EDA Dashboard Tab** (`load_dataset()` function)
Files needed (all must be in `/opt/app/`):
- ✅ `X_train_final.csv` - Standardized/encoded training features (13,333 rows)
- ✅ `y_train_final.csv` - Training labels (0=Low, 1=Medium, 2=High)
- ✅ `X_test_final.csv` - Standardized/encoded test features (3,333 rows)
- ✅ `y_test_final.csv` - Test labels (0=Low, 1=Medium, 2=High)

### 2. **Prediction Tab - Feature Breakdown Bar Colors** (`compute_feature_thresholds()` function)
Files needed (all must be in `/opt/app/`):
- ✅ `dating_app_behavior_dataset.csv` - RAW (original) data to calculate feature statistics (mean, std)
- App uses: mean ± 0.3*std to determine color thresholds (Green/Orange/Red)

### 3. **Model & Preprocessing**
- ✅ `final_autosklearn_model.pkl` - Trained Auto-sklearn model
- ✅ `deployment_artifacts/ordinal_encoder.pkl` - Ordinal encoder for income/education
- ✅ `deployment_artifacts/standard_scaler.pkl` - Standard scaler for numerical features
- ✅ `deployment_artifacts/feature_columns.json` - List of expected feature columns
- ✅ `deployment_artifacts/engagement_mapping.json` - Mapping (0=Low, 1=Medium, 2=High)

## Dockerfile Status
✅ **All files are already included in COPY statements**
```dockerfile
COPY X_train_final.csv ./
COPY y_train_final.csv ./
COPY X_test_final.csv ./
COPY y_test_final.csv ./
COPY dating_app_behavior_dataset.csv ./
```

## Cloud Shell Verification Commands

### 1. **Check Files Exist in Built Container**
Run these commands in Cloud Shell after building the image:

```bash
# List all files in /opt/app directory
docker run <IMAGE_URI> ls -lah /opt/app/

# Verify specific CSV files (one command to check all)
docker run <IMAGE_URI> sh -c "ls -lh /opt/app/*.csv && ls -lh /opt/app/deployment_artifacts/"

# Check total size of CSVs
docker run <IMAGE_URI> sh -c "du -sh /opt/app/*.csv"
```

### 2. **Check File Integrity (First Few Lines)**
```bash
# Verify X_train_final.csv has data
docker run <IMAGE_URI> sh -c "head -2 /opt/app/X_train_final.csv | wc -l"

# Verify y_train_final.csv
docker run <IMAGE_URI> sh -c "head -2 /opt/app/y_train_final.csv | wc -l"

# Check dating_app_behavior_dataset.csv exists and is not empty
docker run <IMAGE_URI> sh -c "wc -l /opt/app/dating_app_behavior_dataset.csv"
```

### 3. **Verify Container Can Load Files (Test Import)**
```bash
docker run <IMAGE_URI> python3 -c "
import pandas as pd
import os
print('Checking files in /opt/app:')
for f in ['X_train_final.csv', 'y_train_final.csv', 'X_test_final.csv', 'y_test_final.csv', 'dating_app_behavior_dataset.csv']:
    path = f'/opt/app/{f}'
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f'✓ {f}: {df.shape}')
    else:
        print(f'✗ {f}: NOT FOUND')
"
```

## How to Deploy Latest Image (No Cache)

### Method 1: Using `gcloud builds submit` (Recommended)
```bash
# From your project directory
gcloud builds submit --tag gcr.io/<PROJECT_ID>/<IMAGE_NAME> --no-cache
```

### Method 2: Force Redeploy Service with Latest Image
```bash
# Deploy to Cloud Run with latest image (no cache)
gcloud run deploy <SERVICE_NAME> \
  --image gcr.io/<PROJECT_ID>/<IMAGE_NAME> \
  --platform managed \
  --region <REGION> \
  --memory 2Gi \
  --cpu 1 \
  --no-traffic  # Optional: deploy but don't route traffic immediately
```

### Method 3: Check Current Deployed Revision
```bash
# List all revisions of your service
gcloud run revisions list --service=<SERVICE_NAME> --platform=managed --region=<REGION>

# Get details of specific revision
gcloud run revisions describe <REVISION_NAME> --service=<SERVICE_NAME> --platform=managed --region=<REGION>

# Get URL of current service
gcloud run services describe <SERVICE_NAME> --platform=managed --region=<REGION>
```

### Method 4: Force Traffic to Specific Revision
```bash
# Route 100% traffic to latest revision (after deploying new image)
gcloud run services update-traffic <SERVICE_NAME> --to-revisions LATEST=100 --platform=managed --region=<REGION>

# Or route to specific revision by name
gcloud run services update-traffic <SERVICE_NAME> --to-revisions <REVISION_NAME>=100 --platform=managed --region=<REGION>
```

## Step-by-Step Cloud Run Deployment

### 1. **Build Image (without cache)**
```bash
gcloud builds submit \
  --tag gcr.io/<PROJECT_ID>/<IMAGE_NAME>:latest \
  --no-cache \
  --timeout=2400s
```

### 2. **Verify Files in Image**
```bash
# Get the full image URI from build output, then run:
docker run gcr.io/<PROJECT_ID>/<IMAGE_NAME>:latest sh -c "ls -lh /opt/app/*.csv"
```

### 3. **Deploy to Cloud Run**
```bash
gcloud run deploy swipe-signals \
  --image gcr.io/<PROJECT_ID>/<IMAGE_NAME>:latest \
  --platform managed \
  --region asia-southeast1 \
  --memory 2Gi \
  --cpu 1 \
  --allow-unauthenticated
```

### 4. **Verify Deployment Logs**
```bash
# View live logs
gcloud run logs read swipe-signals --platform managed --region asia-southeast1 --limit 50 --follow

# Or view in Cloud Logging dashboard
# Cloud Console > Cloud Run > swipe-signals > Logs
```

### 5. **Test App is Accessible**
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe swipe-signals \
  --platform managed \
  --region asia-southeast1 \
  --format='value(status.url)')

# Test it's running
curl $SERVICE_URL
```

## Troubleshooting

### If EDA shows "files missing" error:
1. Check: `gcloud run logs read swipe-signals --limit 100`
2. Verify: `docker run <IMAGE_URI> sh -c "ls /opt/app/*.csv"`
3. Solution: Rebuild with `--no-cache` flag

### If Feature Colors are all the same:
1. Check if `dating_app_behavior_dataset.csv` is in container
2. Verify CSV has the correct columns
3. Check logs: `gcloud run logs read swipe-signals --limit 50`

### If Cloud Run still using old image:
1. Check current revision: `gcloud run revisions list --service=swipe-signals`
2. Force traffic to LATEST: `gcloud run services update-traffic swipe-signals --to-revisions LATEST=100`
3. Or explicitly specify image with `:latest` tag in deploy command

## Environment Variables
```bash
# Cloud Run automatically sets:
PORT=8080  # Dockerfile uses ${PORT:-8080}

# App uses hardcoded paths:
MODEL_PATH='/opt/app/final_autosklearn_model.pkl'
DEPLOY_ARTIFACTS_DIR='/opt/app/deployment_artifacts'
```
