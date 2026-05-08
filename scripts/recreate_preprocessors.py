import json
import os

import joblib
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

WORKDIR = '/opt/app'
DEPLOY_DIR = os.path.join(WORKDIR, 'deployment_artifacts')
os.makedirs(DEPLOY_DIR, exist_ok=True)

RAW_CANDIDATES = [
    os.path.join(WORKDIR, 'dating_app_behavior_dataset.csv'),
    os.path.join(WORKDIR, 'dating_app_behaviour_dataset.csv'),
]

raw_path = next((p for p in RAW_CANDIDATES if os.path.exists(p)), None)
if raw_path is None:
    raise FileNotFoundError('Raw dataset not found. Expected dating_app_behavior_dataset.csv or dating_app_behaviour_dataset.csv')

print('Loading raw dataset:', raw_path)
df = pd.read_csv(raw_path)
print('Raw shape:', df.shape)

# Keep only feature columns used for training/inference.
drop_if_present = ['match_outcome', 'app_usage_time_label', 'swipe_right_label']
for col in drop_if_present:
    if col in df.columns:
        df = df.drop(columns=[col])

print('After dropping non-feature columns:', df.shape)

# 1) Multi-hot encode interests.
interest_dummies = df['interest_tags'].fillna('').str.get_dummies(sep=', ')
interest_dummies = interest_dummies.add_prefix('interest_')
df = pd.concat([df.drop(columns=['interest_tags']), interest_dummies], axis=1)
print(f'✅ Interest tags expanded into {interest_dummies.shape[1]} columns')

# 2) Ordinal encode income and education with fixed category order.
income_order = ['Very Low', 'Low', 'Lower-Middle', 'Middle', 'Upper-Middle', 'High', 'Very High']
education_order = ['No Formal Education', 'High School', 'Diploma', 'Associate’s', 'Bachelor’s', 'MBA', 'Master’s', 'PhD', 'Postdoc']

ord_enc = OrdinalEncoder(
    categories=[income_order, education_order],
    handle_unknown='use_encoded_value',
    unknown_value=-1,
)
df[['income_bracket', 'education_level']] = ord_enc.fit_transform(df[['income_bracket', 'education_level']])

ord_path = os.path.join(DEPLOY_DIR, 'ordinal_encoder.pkl')
joblib.dump(ord_enc, ord_path)
print('Saved ordinal encoder to', ord_path)

# 3) One-hot encode nominal categoricals.
one_hot_cols = ['gender', 'sexual_orientation', 'location_type', 'swipe_time_of_day']
df = pd.get_dummies(df, columns=one_hot_cols, drop_first=True, dtype=int)
print('✅ One-hot encoding done')
print('Encoded shape:', df.shape)

# 4) Fit scaler on notebook numeric columns.
behavioral_feats = [
    'likes_received',
    'mutual_matches',
    'profile_pics_count',
    'bio_length',
    'message_sent_count',
    'emoji_usage_rate',
    'swipe_right_ratio',
]
numeric_cols = ['app_usage_time_min', 'last_active_hour', 'income_bracket', 'education_level'] + behavioral_feats
numeric_cols = [col for col in numeric_cols if col in df.columns]

scaler = StandardScaler()
scaler.fit(df[numeric_cols])

scaler_path = os.path.join(DEPLOY_DIR, 'standard_scaler.pkl')
joblib.dump(scaler, scaler_path)
print(f'Saved standard scaler to {scaler_path} (n_features_in_={scaler.n_features_in_})')

# Save final ordered feature list used by app before scaling.
feat_path = os.path.join(DEPLOY_DIR, 'feature_columns.json')
with open(feat_path, 'w') as f:
    json.dump(df.columns.tolist(), f)
print('Saved feature columns to', feat_path)
