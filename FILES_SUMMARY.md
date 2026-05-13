# Quick Reference: Files Used by EDA & Prediction Features

## EDA Dashboard Tab
**What it does:** Shows class distribution, swipe ratio boxplot, messages histogram, and app usage time boxplot  
**Functions:** `load_dataset()`  
**Files required in `/opt/app/`:**
- ✅ X_train_final.csv (13.66 MB) - used to get features & engagement class
- ✅ y_train_final.csv (0.08 MB) - used to get training labels
- ✅ X_test_final.csv (3.42 MB) - used to get features & engagement class
- ✅ y_test_final.csv (0.02 MB) - used to get test labels

**Status:** ✅ All 4 files copied in Dockerfile (lines 15-18)

---

## Prediction Tab - Feature Breakdown Bar Colors
**What it does:** Dynamic color-coding (Green/Orange/Red) based on feature statistics  
**Functions:** `compute_feature_thresholds()`, `get_feature_color()`  
**Files required in `/opt/app/`:**
- ✅ dating_app_behavior_dataset.csv (7.24 MB) - RAW data for calculating mean & std

**Logic:**
```
Feature threshold = mean ± 0.3*std
- Green (good): value >= mean + 0.3*std
- Orange (avg): value between mean±0.3*std  
- Red (low): value < mean - 0.3*std
```

**Status:** ✅ File copied in Dockerfile (line 19)

---

## Model & Preprocessing (Used by Both Tabs)
**Files required in `/opt/app/`:**
- ✅ final_autosklearn_model.pkl (60.53 MB)
- ✅ deployment_artifacts/ordinal_encoder.pkl
- ✅ deployment_artifacts/standard_scaler.pkl
- ✅ deployment_artifacts/feature_columns.json
- ✅ deployment_artifacts/engagement_mapping.json

**Status:** ✅ All copied in Dockerfile (lines 12, 13, 14)

---

## Dockerfile COPY Statements ✅
```dockerfile
COPY app.py ./
COPY final_autosklearn_model.pkl ./
COPY deployment_artifacts/ ./deployment_artifacts/
COPY X_train_final.csv ./
COPY y_train_final.csv ./
COPY X_test_final.csv ./
COPY y_test_final.csv ./
COPY dating_app_behavior_dataset.csv ./
```

---

## Total Size: ~84.98 MB
Your Docker image should be ~1GB+ (because base image is mfeurer/auto-sklearn:master)
