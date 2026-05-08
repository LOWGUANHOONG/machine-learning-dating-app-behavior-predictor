import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os

# --- Set Page Config FIRST (must be first Streamlit command) ---
st.set_page_config(page_title="Swipe Signals: Dating App Engagement Predictor", layout="wide")

# --- Configuration and File Paths (adjust as needed for your local setup) ---
# Assuming model and preprocessing objects are in the same directory as app.py or a subfolder
# MODEL_PATH = 'final_autosklearn_model.pkl' # Your Auto-sklearn model
# DEPLOY_ARTIFACTS_DIR = 'deployment_artifacts'
MODEL_PATH = '/opt/app/final_autosklearn_model.pkl' # Your Auto-sklearn model
DEPLOY_ARTIFACTS_DIR = '/opt/app/deployment_artifacts'

ORDINAL_ENCODER_PATH = os.path.join(DEPLOY_ARTIFACTS_DIR, 'ordinal_encoder.pkl')
SCALER_PATH = os.path.join(DEPLOY_ARTIFACTS_DIR, 'standard_scaler.pkl')
FEATURE_COLUMNS_PATH = os.path.join(DEPLOY_ARTIFACTS_DIR, 'feature_columns.json')
ENGAGEMENT_MAPPING_PATH = os.path.join(DEPLOY_ARTIFACTS_DIR, 'engagement_mapping.json')

# --- Load Model and Preprocessing Objects ---
@st.cache_resource # Cache the model loading for performance
def load_model(path):
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

@st.cache_resource # Cache for preprocessing objects
def load_preprocessing_objects():
    try:
        ordinal_encoder = joblib.load(ORDINAL_ENCODER_PATH)
        scaler = joblib.load(SCALER_PATH)
        with open(FEATURE_COLUMNS_PATH, 'r') as f:
            feature_columns = json.load(f)
        with open(ENGAGEMENT_MAPPING_PATH, 'r') as f:
            reverse_mapping = json.load(f)
        # Convert string keys back to int for reverse_mapping if necessary
        reverse_mapping = {int(k): v for k, v in reverse_mapping.items()}
        return ordinal_encoder, scaler, feature_columns, reverse_mapping
    except Exception as e:
        st.error(f"Error loading preprocessing objects: {e}")
        return None, None, None, None

model = load_model(MODEL_PATH)
ordinal_encoder, scaler, feature_columns, reverse_mapping = load_preprocessing_objects()

if model is None or ordinal_encoder is None or scaler is None or feature_columns is None or reverse_mapping is None:
    st.stop() # Stop if any essential object failed to load

# --- Streamlit App Layout ---
st.title("💘 Swipe Signals 🚨")
st.markdown("Predicting User Engagement Quality on a Dating Platform. 💞")

# --- User Input Sidebar ---
st.sidebar.header("User Profile & Behavior")

# Numerical Inputs (counts and measurements as number_input for exact entry)
app_usage_time_min = st.sidebar.number_input("App Usage Time (minutes)", min_value=0, max_value=300, value=150, step=1)
likes_received = st.sidebar.number_input("Likes Received", min_value=0, max_value=200, value=100, step=1)
mutual_matches = st.sidebar.number_input("Mutual Matches", min_value=0, max_value=30, value=15, step=1)
profile_pics_count = st.sidebar.number_input("Profile Picture Count", min_value=0, max_value=6, value=3, step=1)
bio_length = st.sidebar.number_input("Bio Length (characters)", min_value=0, max_value=500, value=250, step=1)
message_sent_count = st.sidebar.number_input("Messages Sent", min_value=0, max_value=100, value=50, step=1)
last_active_hour = st.sidebar.number_input("Last Active Hour (0-23)", min_value=0, max_value=23, value=12, step=1)

# Ratio inputs (keep as sliders for proportion visualization)
swipe_right_ratio = st.sidebar.slider("Swipe Right Ratio (0-1)", 0.0, 1.0, 0.5, 0.01)
emoji_usage_rate = st.sidebar.slider("Emoji Usage Rate (0-1)", 0.0, 0.74, 0.28, 0.01)

# Categorical Inputs
gender = st.sidebar.selectbox("Gender", ['Female', 'Male', 'Non-binary', 'Genderfluid', 'Transgender', 'Prefer Not to Say'])
sexual_orientation = st.sidebar.selectbox("Sexual Orientation", ['Straight', 'Bisexual', 'Gay', 'Lesbian', 'Pansexual', 'Asexual', 'Demisexual', 'Queer'])
location_type = st.sidebar.selectbox("Location Type", ['Urban', 'Suburban', 'Metro', 'Small Town', 'Rural', 'Remote Area'])
income_bracket = st.sidebar.selectbox("Income Bracket", ['Very Low', 'Low', 'Lower-Middle', 'Middle', 'Upper-Middle', 'High', 'Very High'])
education_level = st.sidebar.selectbox("Education Level", ['No Formal Education', 'High School', 'Diploma', 'Associate’s', 'Bachelor’s', 'MBA', 'Master’s', 'PhD', 'Postdoc'])
swipe_time_of_day = st.sidebar.selectbox("Swipe Time of Day", ['Morning', 'Afternoon', 'Evening', 'Late Night', 'After Midnight', 'Early Morning'])

# Interest Tags (Multi-select)
# Ensure these are the same as the ones used in training
all_interest_tags = ['Anime', 'Art', 'Astrology', 'Binge-Watching', 'Board Games', 'Cars', 'Clubbing',
                     'Coding', 'Cooking', 'Crafting', 'DIY', 'Dancing', 'Fashion', 'Fitness', 'Foodie',
                     'Gaming', 'Gardening', 'Hiking', 'History', 'Investing', 'K-pop', 'Languages', 'MMA',
                     'Makeup', 'Meditation', 'Memes', 'Motorcycling', 'Movies', 'Music', 'Painting',
                     'Parenting', 'Pets', 'Photography', 'Podcasts', 'Poetry', 'Politics', 'Reading',
                     'Running', 'Skating', 'Sneaker Culture', 'Social Activism', 'Spirituality',
                     'Stand-up Comedy', 'Startups', 'Tattoos', 'Tech', 'Traveling', 'Writing', 'Yoga']
selected_interests = st.sidebar.multiselect("Interest Tags", all_interest_tags)

BEHAVIORAL_FEATS = [
    'likes_received',
    'mutual_matches',
    'profile_pics_count',
    'bio_length',
    'message_sent_count',
    'emoji_usage_rate',
    'swipe_right_ratio',
]


# --- Prediction Function ---
def preprocess_and_predict(user_inputs):
    # Create a DataFrame from current inputs, mirroring the original df structure before encoding
    data = {
        'gender': [user_inputs['gender']],
        'sexual_orientation': [user_inputs['sexual_orientation']],
        'location_type': [user_inputs['location_type']],
        'income_bracket': [user_inputs['income_bracket']],
        'education_level': [user_inputs['education_level']],
        'interest_tags': [', '.join(user_inputs['interest_tags'])] if user_inputs['interest_tags'] else [''],
        'app_usage_time_min': [user_inputs['app_usage_time_min']],
        'swipe_right_ratio': [user_inputs['swipe_right_ratio']],
        'likes_received': [user_inputs['likes_received']],
        'mutual_matches': [user_inputs['mutual_matches']],
        'profile_pics_count': [user_inputs['profile_pics_count']],
        'bio_length': [user_inputs['bio_length']],
        'message_sent_count': [user_inputs['message_sent_count']],
        'emoji_usage_rate': [user_inputs['emoji_usage_rate']],
        'last_active_hour': [user_inputs['last_active_hour']],
        'swipe_time_of_day': [user_inputs['swipe_time_of_day']],
    }
    input_df = pd.DataFrame(data)

    # 1. Multi-hot encode interest_tags from sidebar input.
    # Selected interests are set to 1, all others remain 0.
    selected = user_inputs.get('interest_tags', []) or []
    interest_cols = [f'interest_{tag}' for tag in all_interest_tags]
    interest_dummies = pd.DataFrame(0, index=input_df.index, columns=interest_cols)
    for tag in selected:
        col = f'interest_{tag}'
        if col in interest_dummies.columns:
            interest_dummies.loc[0, col] = 1
    input_df = pd.concat([input_df.drop(columns=['interest_tags']), interest_dummies], axis=1)

    # 2. Ordinal Encoding for income_bracket and education_level
    # Make sure categories are ordered correctly as in training
    ordinal_cols = ['income_bracket', 'education_level']
    input_df[ordinal_cols] = ordinal_encoder.transform(input_df[ordinal_cols])

    # 3. One-hot encode categorical features for a single row.
    # Using get_dummies(drop_first=True) on one row drops all categorical columns,
    # so we map the selected category directly to the expected model column names.
    one_hot_cols_original = ['gender', 'sexual_orientation', 'location_type', 'swipe_time_of_day']
    for col in one_hot_cols_original:
        selected_value = str(input_df.loc[0, col])
        encoded_col = f'{col}_{selected_value}'
        if encoded_col in feature_columns:
            input_df[encoded_col] = 1
    input_df = input_df.drop(columns=one_hot_cols_original)

    # Ensure all expected feature columns are present and in the correct order
    # This handles missing dummy columns for unseen categories
    processed_input = input_df.reindex(columns=feature_columns, fill_value=0)

    # 4. Scale numerical features
    numeric_cols_to_scale = ['app_usage_time_min', 'last_active_hour', 'income_bracket', 'education_level'] + BEHAVIORAL_FEATS

    # Filter numeric_cols_to_scale to only include columns that actually exist in processed_input
    existing_numeric_cols = [col for col in numeric_cols_to_scale if col in processed_input.columns]

    if existing_numeric_cols:
        processed_input[existing_numeric_cols] = scaler.transform(processed_input[existing_numeric_cols])

    # Make prediction
    prediction = model.predict(processed_input)
    prediction_proba = model.predict_proba(processed_input)

    return prediction[0], prediction_proba[0]

# --- Prediction Button and Output ---
if st.sidebar.button("Predict Engagement"):
    user_inputs = {
        'gender': gender,
        'sexual_orientation': sexual_orientation,
        'location_type': location_type,
        'income_bracket': income_bracket,
        'education_level': education_level,
        'interest_tags': selected_interests,
        'app_usage_time_min': app_usage_time_min,
        'swipe_right_ratio': swipe_right_ratio,
        'likes_received': likes_received,
        'mutual_matches': mutual_matches,
        'profile_pics_count': profile_pics_count,
        'bio_length': bio_length,
        'message_sent_count': message_sent_count,
        'emoji_usage_rate': emoji_usage_rate,
        'last_active_hour': last_active_hour,
        'swipe_time_of_day': swipe_time_of_day,
    }

    pred_class_idx, pred_proba = preprocess_and_predict(user_inputs)
    pred_class_label = reverse_mapping.get(pred_class_idx, "Unknown")

    st.subheader("Prediction Results")
    if pred_class_label == 'Low':
        st.error(f"Predicted Engagement: **{pred_class_label}**")
    elif pred_class_label == 'Medium':
        st.warning(f"Predicted Engagement: **{pred_class_label}**")
    else:
        st.success(f"Predicted Engagement: **{pred_class_label}**")

    st.write("\n")
    st.subheader("Prediction Probabilities:")
    proba_df = pd.DataFrame({
        'Engagement Class': [reverse_mapping[i] for i in sorted(reverse_mapping.keys())],
        'Probability': pred_proba
    })
    st.dataframe(proba_df.set_index('Engagement Class'))

st.markdown("--- ")
st.markdown("Developed by WIA1006 OCC11 G13")
st.markdown("""
- Low Guan Hoong
- Tan Dao Phang
- Teow Yan Ping
- Tan Swee Xin
- Lu Jia Kent
- Tan Li Hong
""")