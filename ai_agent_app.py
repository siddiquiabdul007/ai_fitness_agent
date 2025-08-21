import streamlit as st
import os
import requests
import json
import re
import pandas as pd
import altair as alt

# --- App Configuration ---
st.set_page_config(
    page_title="AI Fitness Instructor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- State Management ---
# Initialize session state for user data and progress
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'age': 25, 'gender': 'Male', 'height': 170, 'weight': 70,
        'diet_pref': 'No Preference', 'target': 'Weight Loss', 'conditions': ''
    }
if 'progress_log' not in st.session_state:
    st.session_state.progress_log = pd.DataFrame(columns=['Date', 'Weight'])
if 'plan_data' not in st.session_state:
    st.session_state.plan_data = None


# --- API Configuration and Call ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def get_ai_plan(user_info, history=""):
    """Generates a personalized health plan using the Gemini API."""
    if not GEMINI_API_KEY:
        st.error("Gemini API key is not set. Please add it to your Streamlit secrets.")
        return None

    prompt_text = f"""
    Act as an expert AI Fitness Instructor. Based on the user's details, create a professional, detailed, and encouraging personalized plan.

    User Details:
    - Age: {user_info['age']}
    - Gender: {user_info['gender']}
    - BMI: {user_info['bmi']:.2f}
    - Medical Conditions: {user_info['medical']}
    - Diet Preference: {user_info['diet_pref']}
    - Primary Goal: {user_info['target']}
    {history}

    Task:
    Create a comprehensive diet and gym plan.

    Instructions:
    1.  **Diet Plan:** Provide a detailed meal plan with calorie/macro estimates. Include a variety of options for each meal and emphasize principles like hydration and portion control.
    2.  **Gym Plan:** Create a structured weekly workout schedule. For each exercise, include sets, reps, rest times, and a brief, clear description of the proper form.
    3.  **Tone:** Be encouraging, knowledgeable, and motivational.
    4.  **Format:** Respond with a single JSON object with two keys: "diet_plan" and "gym_plan". The value for each should be a Markdown-formatted string.
    """

    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        plan_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        
        if plan_text.strip().startswith("```json"):
            plan_text = plan_text.strip()[7:-4]
        
        plan_text = re.sub(r',\s*([}\]])', r'\1', plan_text)
        return json.loads(plan_text)

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        st.error(f"Failed to parse the AI's response. Error: {e}")
        st.text_area("Raw AI Response:", value=response.text if 'response' in locals() else "No response", height=200)
    return None

# --- UI Components ---

def display_sidebar():
    """Manages all the inputs in the sidebar."""
    with st.sidebar:
        st.header("👤 Your Profile")
        
        # Load from session state
        ud = st.session_state.user_data

        age = st.number_input("Age", 1, 100, ud['age'])
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(ud['gender']))
        height = st.slider("Height (cm)", 100, 220, ud['height'])
        weight = st.slider("Weight (kg)", 30, 200, ud['weight'])

        if height > 0:
            bmi = round(weight / ((height / 100) ** 2), 2)
            st.metric(label="Your BMI", value=bmi)
        else:
            bmi = 0

        st.subheader("🎯 Health & Goals")
        diet_pref = st.selectbox("Diet Preference", ["No Preference", "Vegetarian", "Vegan", "Non-Vegetarian"], index=["No Preference", "Vegetarian", "Vegan", "Non-Vegetarian"].index(ud['diet_pref']))
        target = st.selectbox("Primary Goal", ["Weight Loss", "Muscle Gain", "Maintain Weight", "Improve Fitness"], index=["Weight Loss", "Muscle Gain", "Maintain Weight", "Improve Fitness"].index(ud['target']))
        conditions = st.text_area("Medical Conditions (if any)", ud['conditions'], placeholder="e.g., Diabetes, allergies...")

        st.markdown("---")
        if st.button("✨ Generate My Plan", use_container_width=True, type="primary"):
            # Save to session state before generating
            st.session_state.user_data = {
                'age': age, 'gender': gender, 'height': height, 'weight': weight,
                'diet_pref': diet_pref, 'target': target, 'conditions': conditions
            }
            user_info = st.session_state.user_data
            user_info['bmi'] = bmi
            user_info['medical'] = conditions if conditions else "None"
            
            with st.spinner("Your AI instructor is creating your plan..."):
                st.session_state.plan_data = get_ai_plan(user_info)

        st.markdown("---")
        st.info("Always consult a professional before starting a new health regimen.")

def display_progress_tracker():
    """Displays UI for logging weight and showing progress chart."""
    st.header("📈 Progress Tracker")
    
    with st.form("progress_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            # FIX: Cast the 'value' to a float to match the other numeric types.
            new_weight = st.number_input("Today's Weight (kg)", min_value=30.0, max_value=200.0, value=float(st.session_state.user_data['weight']), step=0.1)
        with col2:
            log_date = st.date_input("Date")
        
        submitted = st.form_submit_button("Log Weight")
        if submitted:
            new_entry = pd.DataFrame([{'Date': log_date, 'Weight': new_weight}])
            st.session_state.progress_log = pd.concat([st.session_state.progress_log, new_entry], ignore_index=True)
            st.success(f"Logged {new_weight} kg for {log_date}.")

    if not st.session_state.progress_log.empty:
        st.session_state.progress_log['Date'] = pd.to_datetime(st.session_state.progress_log['Date'])
        chart = alt.Chart(st.session_state.progress_log).mark_line(point=True).encode(
            x=alt.X('Date', title='Date'),
            y=alt.Y('Weight', title='Weight (kg)', scale=alt.Scale(zero=False)),
            tooltip=['Date', 'Weight']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

# --- Main App Layout ---

st.title("🤖 AI Fitness Instructor")
st.markdown("Your professional AI partner for personalized diet and gym plans. Fill out your profile in the sidebar to begin!")

display_sidebar()

if st.session_state.plan_data:
    st.success("✅ Your personalized plan is ready! You can find it below.")
    
    tab1, tab2 = st.tabs(["🥗 Diet Plan", "💪 Gym/Exercise Plan"])
    
    with tab1:
        st.markdown(st.session_state.plan_data.get("diet_plan", "No diet plan generated."))
    
    with tab2:
        st.markdown(st.session_state.plan_data.get("gym_plan", "No gym/exercise plan generated."))

    with st.expander("Download Your Plan"):
        full_plan_text = f"--- DIET PLAN ---\n\n{st.session_state.plan_data.get('diet_plan', '')}\n\n--- GYM/EXERCISE PLAN ---\n\n{st.session_state.plan_data.get('gym_plan', '')}"
        st.download_button(
            label="📥 Download Full Plan (.txt)",
            data=full_plan_text,
            file_name="ai_fitness_plan.txt",
            mime="text/plain"
        )
    
    display_progress_tracker()

else:
    st.info("Your generated plan will appear here.")
