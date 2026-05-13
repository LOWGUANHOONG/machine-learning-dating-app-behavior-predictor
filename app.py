import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os
import matplotlib.pyplot as plt

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
@st.cache_resource
def load_model(path):
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

@st.cache_resource
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

with st.sidebar.form("prediction_inputs_form"):
    # Username input (optional, for context/tracking only)
    username = st.text_input("Username (optional)", value="Guest", placeholder="Enter username or leave as Guest")

    # Numerical Inputs (counts and measurements as number_input for exact entry)
    app_usage_time_min = st.number_input("App Usage Time (minutes)", min_value=0, max_value=1440, value=150, step=1)
    likes_received = st.number_input("Likes Received", min_value=0, max_value=500, value=100, step=1)
    mutual_matches = st.number_input("Mutual Matches", min_value=0, max_value=100, value=15, step=1)
    profile_pics_count = st.number_input("Profile Picture Count", min_value=0, max_value=10, value=3, step=1)
    bio_length = st.number_input("Bio Length (characters)", min_value=0, max_value=500, value=250, step=1)
    message_sent_count = st.number_input("Messages Sent", min_value=0, max_value=200, value=50, step=1)
    last_active_hour = st.number_input("Last Active Hour (0-23)", min_value=0, max_value=48, value=12, step=1)

    # Ratio inputs (keep as sliders for proportion visualization)
    swipe_right_ratio = st.slider("Swipe Right Ratio (0-1)", 0.0, 1.0, 0.5, 0.01)
    emoji_usage_rate = st.slider("Emoji Usage Rate (0-1)", 0.0, 0.74, 0.28, 0.01)

    # Categorical Inputs
    gender = st.selectbox("Gender", ['Female', 'Male', 'Non-binary', 'Genderfluid', 'Transgender', 'Prefer Not to Say'])
    sexual_orientation = st.selectbox("Sexual Orientation", ['Straight', 'Bisexual', 'Gay', 'Lesbian', 'Pansexual', 'Asexual', 'Demisexual', 'Queer'])
    location_type = st.selectbox("Location Type", ['Urban', 'Suburban', 'Metro', 'Small Town', 'Rural', 'Remote Area'])
    income_bracket = st.selectbox("Income Bracket", ['Very Low', 'Low', 'Lower-Middle', 'Middle', 'Upper-Middle', 'High', 'Very High'])
    education_level = st.selectbox("Education Level", ['No Formal Education', 'High School', 'Diploma', 'Associate’s', 'Bachelor’s', 'MBA', 'Master’s', 'PhD', 'Postdoc'])
    swipe_time_of_day = st.selectbox("Swipe Time of Day", ['Morning', 'Afternoon', 'Evening', 'Late Night', 'After Midnight', 'Early Morning'])

    # Interest Tags (Multi-select)
    # Ensure these are the same as the ones used in training
    all_interest_tags = ['Anime', 'Art', 'Astrology', 'Binge-Watching', 'Board Games', 'Cars', 'Clubbing',
                         'Coding', 'Cooking', 'Crafting', 'DIY', 'Dancing', 'Fashion', 'Fitness', 'Foodie',
                         'Gaming', 'Gardening', 'Hiking', 'History', 'Investing', 'K-pop', 'Languages', 'MMA',
                         'Makeup', 'Meditation', 'Memes', 'Motorcycling', 'Movies', 'Music', 'Painting',
                         'Parenting', 'Pets', 'Photography', 'Podcasts', 'Poetry', 'Politics', 'Reading',
                         'Running', 'Skating', 'Sneaker Culture', 'Social Activism', 'Spirituality',
                         'Stand-up Comedy', 'Startups', 'Tattoos', 'Tech', 'Traveling', 'Writing', 'Yoga']
    selected_interests = st.multiselect("Interest Tags", all_interest_tags)

    predict_clicked = st.form_submit_button("Predict Engagement")

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

# --- Module-level constants (shared across tabs) ---
_CLASS_COLORS = {'Low': '#e74c3c', 'Medium': '#f39c12', 'High': '#2ecc71'}
_CLASS_DESCRIPTIONS = {
    'High': "This user is highly active — frequent swipes, messages, and strong match quality.",
    'Medium': "This user shows moderate activity — engaged but with room to grow.",
    'Low': "This user shows low activity — infrequent interactions and limited engagement.",
}
_FEAT_MAX = {
    'likes_received': 500, 'mutual_matches': 100, 'message_sent_count': 200,
    'profile_pics_count': 10, 'bio_length': 500, 'swipe_right_ratio': 1.0, 'emoji_usage_rate': 0.74,
}
_CLASS_ORDER = ['Low', 'Medium', 'High']

# --- EDA Dataset Loader ---
# Calculate feature averages for color thresholding in feature breakdown
@st.cache_data
def compute_feature_thresholds():
    """Calculate feature thresholds from RAW (original) data, not standardized.
    This allows meaningful color comparison with raw slider inputs."""
    try:
        def first_existing(paths):
            for p in paths:
                if os.path.exists(p):
                    return p
            return None

        # Try to load original raw dataset for accurate statistics
        raw_data_path = first_existing(['/opt/app/dating_app_behavior_dataset.csv', 'dating_app_behavior_dataset.csv'])
        
        if raw_data_path:
            data = pd.read_csv(raw_data_path)
        else:
            # Fallback: use processed data (less ideal but works)
            x_train_path = first_existing(['/opt/app/X_train_final.csv', 'X_train_final.csv'])
            x_test_path = first_existing(['/opt/app/X_test_final.csv', 'X_test_final.csv'])
            if not all([x_train_path, x_test_path]):
                return None
            x_train = pd.read_csv(x_train_path)
            x_test = pd.read_csv(x_test_path)
            data = pd.concat([x_train, x_test], ignore_index=True)
        
        thresholds = {}
        for feat in BEHAVIORAL_FEATS:
            if feat in data.columns:
                mean = data[feat].mean()
                std = data[feat].std()
                thresholds[feat] = {'mean': mean, 'std': std}
        return thresholds
    except Exception as e:
        return None

def get_feature_color(feature_name, feature_value, thresholds):
    """Determine color based on how the feature value compares to dataset statistics.
    Green: above-average (>= mean + 0.3*std) | Orange: average (between mean±0.3*std) | Red: below-average"""
    if not thresholds or feature_name not in thresholds:
        return '#95a5a6'
    mean = thresholds[feature_name]['mean']
    std = thresholds[feature_name]['std']
    
    # Handle edge case where std is 0
    if std == 0:
        return '#f39c12' if feature_value == mean else ('#2ecc71' if feature_value > mean else '#e74c3c')
    
    if feature_value >= mean + 0.3 * std:
        return '#2ecc71'  # Green: above average
    elif feature_value >= mean - 0.3 * std:
        return '#f39c12'  # Orange: within average range
    else:
        return '#e74c3c'  # Red: below average

@st.cache_data
def load_dataset():
    try:
        def first_existing(paths):
            for p in paths:
                if os.path.exists(p):
                    return p
            return None

        x_train_path = first_existing(['/opt/app/X_train_final.csv', 'X_train_final.csv'])
        y_train_path = first_existing(['/opt/app/y_train_final.csv', 'y_train_final.csv'])
        x_test_path = first_existing(['/opt/app/X_test_final.csv', 'X_test_final.csv'])
        y_test_path = first_existing(['/opt/app/y_test_final.csv', 'y_test_final.csv'])

        if not all([x_train_path, y_train_path, x_test_path, y_test_path]):
            st.error("Processed EDA files are missing. Expected X_train_final.csv, y_train_final.csv, X_test_final.csv, y_test_final.csv")
            return None

        x_train = pd.read_csv(x_train_path)
        y_train = pd.read_csv(y_train_path)
        x_test = pd.read_csv(x_test_path)
        y_test = pd.read_csv(y_test_path)

        target_col = 'engagement_class' if 'engagement_class' in y_train.columns else y_train.columns[0]
        train_df = x_train.copy()
        test_df = x_test.copy()
        train_df['engagement_class'] = pd.to_numeric(y_train[target_col], errors='coerce')
        test_df['engagement_class'] = pd.to_numeric(y_test[target_col], errors='coerce')

        df = pd.concat([train_df, test_df], ignore_index=True)
        df = df[df['engagement_class'].notna()].copy()
        df['engagement_class'] = df['engagement_class'].astype(int)
        df['engagement_label'] = df['engagement_class'].map(reverse_mapping)

        unknown_count = int(df['engagement_label'].isna().sum())
        if unknown_count > 0:
            st.warning(f"{unknown_count} rows have class IDs not found in engagement mapping and are excluded from charts.")
            df = df[df['engagement_label'].notna()]

        return df
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return None

# ============================================================
# Tab Layout
# ============================================================
tab1, tab2, tab3 = st.tabs(["Predictor", "EDA Dashboard", "Model Comparison"])

# ============================================================
# TAB 1 — Predictor
# ============================================================
with tab1:
    if predict_clicked:
        user_inputs = {
            'username': username,
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

        # --- Feature 2: Styled Prediction Result Card ---
        card_color = _CLASS_COLORS.get(pred_class_label, '#95a5a6')
        card_desc = _CLASS_DESCRIPTIONS.get(pred_class_label, "")
        st.markdown(f"""
        <div style="background-color:{card_color}; padding:24px; border-radius:12px; text-align:center;">
            <h2 style="color:white; margin:0;">Predicted Engagement: {pred_class_label}</h2>
            <p style="color:white; font-size:16px; margin-top:8px;">{card_desc}</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        # --- Feature 1: Probability Bar Chart ---
        st.subheader("Prediction Probabilities")
        class_order = [reverse_mapping[i] for i in sorted(reverse_mapping.keys())]
        bar_colors = [_CLASS_COLORS[c] for c in class_order]
        fig1, ax1 = plt.subplots(figsize=(6, 2.5))
        bars = ax1.barh(class_order, pred_proba * 100, color=bar_colors)
        ax1.set_xlim(0, 110)
        ax1.set_xlabel("Probability (%)")
        for bar, pct in zip(bars, pred_proba * 100):
            ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                     f"{pct:.1f}%", va='center', fontsize=10)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

        # --- Feature 3: Input Summary Panel ---
        st.subheader("Your Input Profile")
        summary_items = [
            ("Likes Received", likes_received),
            ("Mutual Matches", mutual_matches),
            ("Messages Sent", message_sent_count),
            ("Profile Pics", profile_pics_count),
            ("Bio Length", bio_length),
            ("Swipe Right Ratio", swipe_right_ratio),
            ("Emoji Usage Rate", emoji_usage_rate),
        ]
        col1, col2 = st.columns(2)
        for i, (label, value) in enumerate(summary_items):
            (col1 if i % 2 == 0 else col2).metric(label, value)

        # --- Feature 4: Engagement Score Breakdown Chart ---
        st.subheader("Engagement Feature Breakdown")
        feat_labels = ['Likes Received', 'Mutual Matches', 'Messages Sent',
                       'Profile Pics', 'Bio Length', 'Swipe Right Ratio', 'Emoji Usage Rate']
        feat_names = ['likes_received', 'mutual_matches', 'message_sent_count',
                      'profile_pics_count', 'bio_length', 'swipe_right_ratio', 'emoji_usage_rate']
        feat_raw = [likes_received, mutual_matches, message_sent_count,
                    profile_pics_count, bio_length, swipe_right_ratio, emoji_usage_rate]
        feat_maxes = [_FEAT_MAX['likes_received'], _FEAT_MAX['mutual_matches'], _FEAT_MAX['message_sent_count'],
                      _FEAT_MAX['profile_pics_count'], _FEAT_MAX['bio_length'],
                      _FEAT_MAX['swipe_right_ratio'], _FEAT_MAX['emoji_usage_rate']]
        normalised = [v / m for v, m in zip(feat_raw, feat_maxes)]
        
        # Compute colors based on feature value thresholds
        thresholds = compute_feature_thresholds()
        bar_colors = [get_feature_color(fname, fval, thresholds) for fname, fval in zip(feat_names, feat_raw)]
        
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.barh(feat_labels, normalised, color=bar_colors)
        ax2.set_xlim(0, 1)
        ax2.set_xlabel("Normalised Score (0–1)")
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)
        
        st.caption("🟢 Green = above average  |  🟠 Orange = average range  |  🔴 Red = below average")

        # --- Feature 5: Append to Prediction History with Auto-Numbered Usernames ---
        if 'prediction_history' not in st.session_state:
            st.session_state.prediction_history = []
        
        # Auto-increment username if duplicate exists
        final_username = username
        existing_usernames = [h['Username'] for h in st.session_state.prediction_history]
        if final_username in existing_usernames:
            count = 1
            while f"{username}{count}" in existing_usernames:
                count += 1
            final_username = f"{username}{count}"
        
        st.session_state.prediction_history.append({
            'Username': final_username,
            'Likes Received': likes_received,
            'Mutual Matches': mutual_matches,
            'Messages Sent': message_sent_count,
            'Swipe Right Ratio': swipe_right_ratio,
            'Emoji Usage Rate': emoji_usage_rate,
            'Predicted Class': pred_class_label,
        })

    # --- Feature 5: Prediction History Table (always visible after first prediction) ---
    if 'prediction_history' in st.session_state and st.session_state.prediction_history:
        st.subheader("Prediction History (This Session)")
        history_df = pd.DataFrame(st.session_state.prediction_history)
        st.dataframe(history_df, use_container_width=True)

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

# ============================================================
# TAB 2 — EDA Dashboard
# ============================================================
with tab2:
    st.subheader("Exploratory Data Analysis")
    df = load_dataset()
    if df is not None:
        st.caption("EDA source: processed features and labels from X_train/X_test and y_train/y_test.")

        col_a, col_b = st.columns(2)

        # Chart 1: Engagement Class Distribution
        with col_a:
            st.markdown("<h3 style='color: #2c3e50; font-weight: bold;'>📊 Engagement Class Distribution</h3>", unsafe_allow_html=True)
            st.caption("Count of users falling into each engagement tier.")
            counts = df['engagement_label'].value_counts().reindex(_CLASS_ORDER, fill_value=0)
            fig_e1, ax_e1 = plt.subplots(figsize=(5, 3))
            ax_e1.barh(_CLASS_ORDER, counts.values,
                       color=[_CLASS_COLORS[c] for c in _CLASS_ORDER])
            ax_e1.set_xlabel("Count")
            for i, v in enumerate(counts.values):
                ax_e1.text(v + 50, i, str(v), va='center', fontsize=9)
            ax_e1.spines['top'].set_visible(False)
            ax_e1.spines['right'].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig_e1)
            plt.close(fig_e1)

        # Chart 2: Swipe Right Ratio by Engagement Class
        with col_b:
            st.markdown("<h3 style='color: #2c3e50; font-weight: bold;'>💬 Swipe Right Ratio by Engagement Class</h3>", unsafe_allow_html=True)
            st.caption("Distribution of swipe selectivity across engagement tiers. Higher engagement classes may show more decisive swiping behavior.")
            data_by_class = [df[df['engagement_label'] == cls]['swipe_right_ratio'].dropna()
                             for cls in _CLASS_ORDER]
            fig_e2, ax_e2 = plt.subplots(figsize=(5, 3))
            bp = ax_e2.boxplot(data_by_class, vert=True, patch_artist=True, labels=_CLASS_ORDER)
            for patch, cls in zip(bp['boxes'], _CLASS_ORDER):
                patch.set_facecolor(_CLASS_COLORS[cls])
                patch.set_alpha(0.7)
            ax_e2.set_ylabel("Swipe Right Ratio")
            ax_e2.set_ylim(-0.2, 1.2)
            ax_e2.spines['top'].set_visible(False)
            ax_e2.spines['right'].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig_e2)
            plt.close(fig_e2)

        col_c, col_d = st.columns(2)

        # Chart 3: Messages Sent Distribution by Class
        with col_c:
            st.markdown("<h3 style='color: #2c3e50; font-weight: bold;'>💌 Messages Sent Distribution by Class</h3>", unsafe_allow_html=True)
            st.caption("Overlapping histograms showing messaging frequency per engagement tier. Higher engagement classes may have larger number of active messages sent.")
            fig_e3, ax_e3 = plt.subplots(figsize=(5, 3))
            for cls in _CLASS_ORDER:
                subset = df[df['engagement_label'] == cls]['message_sent_count'].dropna()
                ax_e3.hist(subset, bins=30, density=True, alpha=0.5,
                           color=_CLASS_COLORS[cls], label=cls)
            ax_e3.set_xlabel("Messages Sent")
            ax_e3.set_ylabel("Density")
            ax_e3.legend()
            ax_e3.spines['top'].set_visible(False)
            ax_e3.spines['right'].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig_e3)
            plt.close(fig_e3)

        # Chart 4: App Usage Time vs Engagement Class
        with col_d:
            st.markdown("<h3 style='color: #2c3e50; font-weight: bold;'>⏱️ App Usage Time vs Engagement Class</h3>", unsafe_allow_html=True)
            st.caption("Distribution of app usage time for each engagement class. Higher app usage time doesn't mean high engagement if the time is not spent effectively (e.g., passive browsing vs active swiping/messaging).")
            data_usage_by_class = [df[df['engagement_label'] == cls]['app_usage_time_min'].dropna()
                                   for cls in _CLASS_ORDER]
            fig_e4, ax_e4 = plt.subplots(figsize=(5, 3))
            bp_usage = ax_e4.boxplot(data_usage_by_class, vert=True, patch_artist=True, labels=_CLASS_ORDER)
            for patch, cls in zip(bp_usage['boxes'], _CLASS_ORDER):
                patch.set_facecolor(_CLASS_COLORS[cls])
                patch.set_alpha(0.7)
            ax_e4.set_ylabel("App Usage Time (standardized)")
            ax_e4.spines['top'].set_visible(False)
            ax_e4.spines['right'].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig_e4)
            plt.close(fig_e4)
    
    st.markdown("--- ")
    st.markdown("<h4 style='text-align: center; color: #555;'>Developed by WIA1006 OCC11 G13</h4>", unsafe_allow_html=True)
    st.markdown("""
- Low Guan Hoong
- Tan Dao Phang
- Teow Yan Ping
- Tan Swee Xin
- Lu Jia Kent
- Tan Li Hong
""")

# ============================================================
# TAB 3 — Model Comparison
# ============================================================
with tab3:
    st.subheader("Model Performance Comparison")

    model_results = pd.DataFrame({
        'Model': ['Auto-sklearn', 'XGBoost', 'Random Forest', 'Neural Network',
                  'SVM', 'Logistic Regression', 'KNN'],
        'Accuracy (%)':  [99.79, 95.85, 89.49, 99.19, 99.49, 99.71, 79.85],
        'Precision (%)': [100.00, 96.00, 90.00, 99.00, 99.00, 100.00, 80.00],
        'Recall (%)':    [100.00, 96.00, 89.00, 99.00, 99.00, 100.00, 80.00],
        'F1 (%)':        [100.00, 96.00, 90.00, 99.00, 99.00, 100.00, 80.00],
    }).sort_values('Accuracy (%)', ascending=False).reset_index(drop=True)

    st.dataframe(model_results.set_index('Model'), use_container_width=True)

    st.markdown(
        "> **Note:** We use the ensemble models created by Auto-sklearn for engagement class prediction as it acquires the highest accuracy score among the manual-tuned models."
    )

    # Horizontal bar chart — sort ascending so highest bar appears at top in barh
    chart_df = model_results.sort_values('Accuracy (%)', ascending=True)
    bar_colors_mc = ['#2ecc71' if m == 'Auto-sklearn' else '#3498db' for m in chart_df['Model']]
    fig_mc, ax_mc = plt.subplots(figsize=(8, 4))
    bars_mc = ax_mc.barh(chart_df['Model'], chart_df['Accuracy (%)'], color=bar_colors_mc)
    ax_mc.set_xlim(0, 115)
    ax_mc.set_xlabel("Accuracy (%)")
    for bar, val in zip(bars_mc, chart_df['Accuracy (%)']):
        ax_mc.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                   f"{val:.2f}%", va='center', fontsize=9)
    ax_mc.spines['top'].set_visible(False)
    ax_mc.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig_mc)
    plt.close(fig_mc)
    
    st.markdown("--- ")
    st.markdown("<h4 style='text-align: center; color: #555;'>Developed by WIA1006 OCC11 G13</h4>", unsafe_allow_html=True)
    st.markdown("""
- Low Guan Hoong
- Tan Dao Phang
- Teow Yan Ping
- Tan Swee Xin
- Lu Jia Kent
- Tan Li Hong
""")