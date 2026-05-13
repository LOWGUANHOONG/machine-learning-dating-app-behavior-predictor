# QUICK REFERENCE: Most Important Commands

## For Your Next Cloud Shell Session

### Copy this entire block and run it

```bash
#!/bin/bash
# Configuration
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="swipe-signals"
REGION="asia-southeast1"
TAG="gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"

echo "════════════════════════════════════════════"
echo "STEP 1: Build Image (NO CACHE - Important!)"
echo "════════════════════════════════════════════"
gcloud builds submit --tag $TAG --no-cache --timeout=2400s

echo -e "\n════════════════════════════════════════════"
echo "STEP 2: Verify CSV Files in Image"
echo "════════════════════════════════════════════"
docker run $TAG sh -c "echo 'CSV Files:' && ls -lh /opt/app/*.csv && echo '' && echo 'File Count:' && wc -l /opt/app/X_train_final.csv /opt/app/dating_app_behavior_dataset.csv"

echo -e "\n════════════════════════════════════════════"
echo "STEP 3: Deploy to Cloud Run"
echo "════════════════════════════════════════════"
gcloud run deploy swipe-signals \
  --image $TAG \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 1 \
  --allow-unauthenticated

echo -e "\n════════════════════════════════════════════"
echo "STEP 4: Get Service URL"
echo "════════════════════════════════════════════"
SERVICE_URL=$(gcloud run services describe swipe-signals \
  --platform managed \
  --region $REGION \
  --format='value(status.url)')
echo "🔗 Service URL: $SERVICE_URL"
echo ""
echo "Test it: curl $SERVICE_URL"

echo -e "\n════════════════════════════════════════════"
echo "STEP 5: Monitor Logs"
echo "════════════════════════════════════════════"
echo "Run this in a new terminal to see real-time logs:"
echo "gcloud run logs read swipe-signals --platform managed --region $REGION --limit 50 --follow"
```

---

## Key Commands You MUST Know

### 1. To build WITHOUT caching (forces latest files)
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/swipe-signals:latest --no-cache --timeout=2400s
```
✅ **This is critical!** Without `--no-cache`, old CSV files might be used from cache

### 2. To verify CSVs are in the built image
```bash
docker run gcr.io/$PROJECT_ID/swipe-signals:latest ls -lh /opt/app/*.csv
```
✅ Should show all 5 files: X_train, y_train, X_test, y_test, dating_app_behavior_dataset

### 3. To deploy to Cloud Run
```bash
gcloud run deploy swipe-signals \
  --image gcr.io/$PROJECT_ID/swipe-signals:latest \
  --platform managed \
  --region asia-southeast1 \
  --memory 2Gi \
  --cpu 1 \
  --allow-unauthenticated
```
✅ Always use `:latest` tag to ensure latest image is deployed

### 4. To check which revision is running
```bash
gcloud run services describe swipe-signals --platform managed --region asia-southeast1 \
  --format='value(status.latestReadyRevisionName)'
```
✅ Use this to verify Cloud Run deployed your new image, not an old one

### 5. To force traffic to latest revision
```bash
gcloud run services update-traffic swipe-signals --to-revisions LATEST=100 --platform managed --region asia-southeast1
```
✅ If Cloud Run is serving old revision, force it to use the latest

### 6. To view real-time logs
```bash
gcloud run logs read swipe-signals --platform managed --region asia-southeast1 --limit 50 --follow
```
✅ Run this in separate terminal while testing to see any errors

---

## What You're Checking For

### When building (Step 2):
```
✓ X_train_final.csv (13.66 MB)
✓ y_train_final.csv (0.08 MB)
✓ X_test_final.csv (3.42 MB)
✓ y_test_final.csv (0.02 MB)
✓ dating_app_behavior_dataset.csv (7.24 MB)
```

### When testing (after deployment):
1. **EDA Dashboard tab** → should show 4 charts with data
2. **Predictor tab** → enter values → feature bars should be Green/Orange/Red (not all one color)
3. **Logs** → no "file not found" or "cannot load" errors

---

## The Most Important Thing: `--no-cache`

**Without it:**
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/swipe-signals:latest
❌ Might use cached old CSV files
❌ Feature colors might be calculated from old data
❌ EDA chart might show old data
```

**With it:**
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/swipe-signals:latest --no-cache
✅ Always copies latest files
✅ Feature colors calculated from current data
✅ EDA charts show current data
```

**Use `--no-cache` every time you deploy!**

---

## Troubleshooting Decision Tree

```
Issue: EDA Tab Error
├─ Check: gcloud run logs read swipe-signals --limit 100
├─ If "cannot find": CSV files not in image
│  └─ Solution: Rebuild with --no-cache
├─ If "No such file": app.py has wrong path
│  └─ Solution: Check paths are /opt/app/ (not local paths)

Issue: Feature Bars All Same Color
├─ Check: docker run $IMAGE python3 -c "import pandas as pd; print(pd.read_csv('/opt/app/dating_app_behavior_dataset.csv').shape)"
├─ If error: File not copied
│  └─ Solution: Rebuild with --no-cache
├─ If OK: Check compute_feature_thresholds() in app.py

Issue: App Showing Old Data
├─ Check: gcloud run revisions list --service swipe-signals
├─ If not LATEST: Traffic routing to old revision
│  └─ Solution: gcloud run services update-traffic swipe-signals --to-revisions LATEST=100
```

---

## Files Your Code Needs (Inside Container)

These must be in `/opt/app/`:
- X_train_final.csv ← for EDA charts
- y_train_final.csv ← for EDA charts
- X_test_final.csv ← for EDA charts
- y_test_final.csv ← for EDA charts
- dating_app_behavior_dataset.csv ← **FOR COLOR THRESHOLDS**
- final_autosklearn_model.pkl ← for predictions
- deployment_artifacts/ ← preprocessing objects

✅ **All in Dockerfile lines 12-19**

---

## One-Command Status Check

```bash
echo "Build status:" && \
gcloud builds log $(gcloud builds list --limit 1 --format='value(id)') --limit 10 | tail -5 && \
echo "" && \
echo "Deployed revision:" && \
gcloud run services describe swipe-signals --platform managed --region asia-southeast1 --format='value(status.latestReadyRevisionName)' && \
echo "" && \
echo "Service URL:" && \
gcloud run services describe swipe-signals --platform managed --region asia-southeast1 --format='value(status.url)'
```

---

## Save This for Your Cloud Shell

Bookmark these commands in your Cloud Shell history or save to a `deploy-checklist.sh`:

1. **Always start with:** `--no-cache` build
2. **Always verify with:** `docker run ... ls -lh /opt/app/*.csv`
3. **Always deploy with:** Latest tag
4. **Always monitor with:** `--follow` logs
5. **Always test:** EDA tab + Predictor tab

You're good to push to GitHub! 🚀
