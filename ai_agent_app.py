import streamlit as st
import requests
import json
import pandas as pd
import altair as alt
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- App Configuration ---
st.set_page_config(
    page_title="FitAI Pro - AI Fitness Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💪"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .feature-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 8px;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    .tab-content {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
# Initialize session state for user data and progress
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'age': 25, 'gender': 'Male', 'height': 170, 'weight': 70,
        'diet_pref': 'No Preference', 'target': 'Weight Loss', 'conditions': ''
    }
if 'progress_log' not in st.session_state:
    st.session_state.progress_log = pd.DataFrame(columns=['Date', 'Weight', 'Body_Fat', 'Muscle_Mass'])
if 'sleep_log' not in st.session_state:
    st.session_state.sleep_log = pd.DataFrame(columns=['Date', 'Sleep_Hours', 'Sleep_Quality', 'Bedtime', 'Wake_Time'])
if 'workout_log' not in st.session_state:
    st.session_state.workout_log = pd.DataFrame(columns=['Date', 'Workout_Type', 'Duration', 'Calories_Burned', 'Notes'])
if 'nutrition_log' not in st.session_state:
    st.session_state.nutrition_log = pd.DataFrame(columns=['Date', 'Meal', 'Calories', 'Protein', 'Carbs', 'Fat', 'Notes'])
if 'plan_data' not in st.session_state:
    st.session_state.plan_data = None
if 'goals' not in st.session_state:
    st.session_state.goals = {
        'target_weight': 65,
        'target_sleep': 8,
        'target_workouts': 4,
        'target_calories': 2000
    }

# --- API Configuration and Call ---
# Ensure you have your GEMINI_API_KEY in Streamlit's secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", None))
# Using a stable, recommended model endpoint
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def validate_user_inputs(age, height, weight):
    """Validate user inputs for reasonable health values."""
    # Ensure all inputs are integers for validation
    try:
        age = int(age)
        height = int(height)
        weight = int(weight)
    except (ValueError, TypeError):
        return False, "Invalid input types. Please enter numeric values."
    
    if age < 13 or age > 100:
        return False, "Age must be between 13 and 100 years."
    if height < 100 or height > 250:
        return False, "Height must be between 100 and 250 cm."
    if weight < 30 or weight > 300:
        return False, "Weight must be between 30 and 300 kg."
    return True, ""

def get_ai_plan(user_info, history=""):
    """Generates a personalized health plan using the Gemini API."""
    if not GEMINI_API_KEY:
        st.error("Gemini API key is not set. Please add it to your Streamlit secrets.")
        return None

    # Ensure all user_info values are properly typed
    try:
        user_info = {
            'age': int(user_info.get('age', 25)),
            'gender': str(user_info.get('gender', 'Male')),
            'bmi': float(user_info.get('bmi', 0.0)),
            'medical': str(user_info.get('medical', 'None')),
            'diet_pref': str(user_info.get('diet_pref', 'No Preference')),
            'target': str(user_info.get('target', 'Weight Loss'))
        }
    except (ValueError, TypeError) as e:
        st.error(f"Invalid user data format: {e}")
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
    {str(history) if history else ""}

    Task:
    Create a comprehensive diet and gym plan.

    Instructions:
    1.  **Diet Plan:** Provide a detailed meal plan with calorie/macro estimates. Include a variety of options for each meal and emphasize principles like hydration and portion control.
    2.  **Gym Plan:** Create a structured weekly workout schedule. For each exercise, include sets, reps, rest times, and a brief, clear description of the proper form.
    3.  **Tone:** Be encouraging, knowledgeable, and motivational.
    4.  **Format:** Respond with a single JSON object with two keys: "diet_plan" and "gym_plan". The value for each should be a Markdown-formatted string. Ensure the JSON is perfectly valid and contains no trailing commas.
    """

    payload = {
        "contents": [{"parts": [{"text": str(prompt_text)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
        }
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": str(GEMINI_API_KEY)}

    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        # Parse the API response properly
        response_data = response.json()
        
        # Handle different response formats from Gemini API
        if "candidates" in response_data:
            # Standard Gemini response format
            plan_text = str(response_data["candidates"][0]["content"]["parts"][0]["text"])
            
            # Clean up the response text
            if plan_text.strip().startswith("```json"):
                plan_text = plan_text.strip()[7:-4]
            elif plan_text.strip().startswith("```"):
                plan_text = plan_text.strip()[3:-3]
            
            # Parse the JSON response
            try:
                plan_json = json.loads(plan_text)
                if "diet_plan" in plan_json and "gym_plan" in plan_json:
                    return plan_json
                else:
                    st.error("API response missing required diet_plan or gym_plan keys")
                    return None
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON response: {e}")
                st.text_area("Raw AI Response:", value=plan_text, height=200)
                return None
        else:
            # Direct JSON response (as configured)
            if "diet_plan" in response_data and "gym_plan" in response_data:
                return response_data
            else:
                st.error("Unexpected API response format")
                st.text_area("Raw API Response:", value=str(response.text), height=200)
                return None

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        st.error(f"Failed to parse the AI's response. Error: {e}")
        if 'response' in locals():
            st.text_area("Raw AI Response:", value=str(response.text), height=200)
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    
    return None

# --- UI Components ---

def display_sidebar():
    """Manages all the inputs in the sidebar."""
    with st.sidebar:
        st.markdown("""
        <div class="main-header">
            <h1>🏃‍♂️ FitAI Pro</h1>
            <p>Your AI Fitness Companion</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("👤 Your Profile")
        
        # Load from session state with type safety
        ud = st.session_state.user_data
        
        # Ensure default values are properly typed
        default_age = int(ud.get('age', 25))
        default_height = int(ud.get('height', 170))
        default_weight = int(ud.get('weight', 70))
        default_gender = str(ud.get('gender', 'Male'))
        default_diet_pref = str(ud.get('diet_pref', 'No Preference'))
        default_target = str(ud.get('target', 'Weight Loss'))
        default_conditions = str(ud.get('conditions', ''))

        age = st.number_input("Age", 13, 100, default_age)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(default_gender))
        height = st.slider("Height (cm)", 100, 250, default_height, step=1)
        weight = st.slider("Weight (kg)", 30, 300, default_weight, step=1)

        # Calculate BMI with safety check and type casting
        if height > 0:
            bmi = round(float(weight) / ((float(height) / 100.0) ** 2), 2)
            
            # BMI category
            if bmi < 18.5:
                bmi_category = "Underweight"
                bmi_color = "red"
            elif bmi < 25:
                bmi_category = "Normal weight"
                bmi_color = "green"
            elif bmi < 30:
                bmi_category = "Overweight"
                bmi_color = "orange"
            else:
                bmi_category = "Obese"
                bmi_color = "red"
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>Your BMI: {bmi}</h4>
                <p style="color: {bmi_color}; font-weight: bold;">{bmi_category}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            bmi = 0.0
            st.error("Invalid height value")

        st.subheader("🎯 Health & Goals")
        diet_pref = st.selectbox("Diet Preference", ["No Preference", "Vegetarian", "Vegan", "Non-Vegetarian"], index=["No Preference", "Vegetarian", "Vegan", "Non-Vegetarian"].index(default_diet_pref))
        target = st.selectbox("Primary Goal", ["Weight Loss", "Muscle Gain", "Maintain Weight", "Improve Fitness"], index=["Weight Loss", "Muscle Gain", "Maintain Weight", "Improve Fitness"].index(default_target))
        conditions = st.text_area("Medical Conditions (if any)", default_conditions, placeholder="e.g., Diabetes, allergies...")

        st.markdown("---")
        if st.button("✨ Generate My Plan", use_container_width=True, type="primary"):
            # Validate inputs before proceeding
            is_valid, error_msg = validate_user_inputs(age, height, weight)
            if not is_valid:
                st.error(error_msg)
                return
            
            # Save to session state before generating with proper type casting
            st.session_state.user_data = {
                'age': int(age),
                'gender': str(gender),
                'height': int(height),
                'weight': int(weight),
                'diet_pref': str(diet_pref),
                'target': str(target),
                'conditions': str(conditions)
            }
            user_info = st.session_state.user_data.copy()
            user_info['bmi'] = float(bmi)
            user_info['medical'] = str(conditions) if conditions else "None"
            
            with st.spinner("Your AI instructor is creating your plan..."):
                st.session_state.plan_data = get_ai_plan(user_info)

        st.markdown("---")
        st.info("Always consult a professional before starting a new health regimen.")

def display_dashboard():
    """Displays the main dashboard with key metrics."""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Fitness Dashboard</h1>
        <p>Track your progress and stay motivated</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_weight = st.session_state.user_data.get('weight', 70)
        target_weight = st.session_state.goals.get('target_weight', 65)
        weight_progress = max(0, min(100, (current_weight - target_weight) / (st.session_state.user_data.get('weight', 70) - target_weight) * 100))
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚖️ Current Weight</h3>
            <h2>{current_weight} kg</h2>
            <p>Target: {target_weight} kg</p>
            <div class="progress-bar" style="width: {weight_progress}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if not st.session_state.sleep_log.empty:
            recent_sleep = st.session_state.sleep_log.iloc[-1]['Sleep_Hours']
            target_sleep = st.session_state.goals.get('target_sleep', 8)
            sleep_progress = min(100, (recent_sleep / target_sleep) * 100)
        else:
            recent_sleep = 0
            sleep_progress = 0
            
        st.markdown(f"""
        <div class="metric-card">
            <h3>😴 Sleep Quality</h3>
            <h2>{recent_sleep:.1f} hrs</h2>
            <p>Target: {st.session_state.goals.get('target_sleep', 8)} hrs</p>
            <div class="progress-bar" style="width: {sleep_progress}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if not st.session_state.workout_log.empty:
            weekly_workouts = len(st.session_state.workout_log[
                st.session_state.workout_log['Date'] >= (datetime.now() - timedelta(days=7)).date()
            ])
            target_workouts = st.session_state.goals.get('target_workouts', 4)
            workout_progress = min(100, (weekly_workouts / target_workouts) * 100)
        else:
            weekly_workouts = 0
            target_workouts = st.session_state.goals.get('target_workouts', 4)
            workout_progress = 0
            
        st.markdown(f"""
        <div class="metric-card">
            <h3>💪 Weekly Workouts</h3>
            <h2>{weekly_workouts}</h2>
            <p>Target: {target_workouts}</p>
            <div class="progress-bar" style="width: {workout_progress}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if not st.session_state.nutrition_log.empty:
            today_calories = st.session_state.nutrition_log[
                st.session_state.nutrition_log['Date'] == date.today()
            ]['Calories'].sum()
            target_calories = st.session_state.goals.get('target_calories', 2000)
            calorie_progress = min(100, (today_calories / target_calories) * 100)
        else:
            today_calories = 0
            target_calories = st.session_state.goals.get('target_calories', 2000)
            calorie_progress = 0
            
        st.markdown(f"""
        <div class="metric-card">
            <h3>🍎 Daily Calories</h3>
            <h2>{today_calories}</h2>
            <p>Target: {target_calories}</p>
            <div class="progress-bar" style="width: {calorie_progress}%"></div>
        </div>
        """, unsafe_allow_html=True)

def display_sleep_tracker():
    """Displays UI for logging sleep and showing sleep analytics."""
    st.header("😴 Sleep Tracker")
    
    with st.form("sleep_form"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sleep_hours = st.number_input("Sleep Hours", 0.0, 24.0, 8.0, 0.5)
        with col2:
            sleep_quality = st.selectbox("Sleep Quality", ["Poor", "Fair", "Good", "Excellent"])
        with col3:
            bedtime = st.time_input("Bedtime", value=datetime.strptime("22:00", "%H:%M").time())
        with col4:
            wake_time = st.time_input("Wake Time", value=datetime.strptime("06:00", "%H:%M").time())
        
        submitted = st.form_submit_button("Log Sleep")
        if submitted:
            new_entry = pd.DataFrame([{
                'Date': date.today(),
                'Sleep_Hours': float(sleep_hours),
                'Sleep_Quality': str(sleep_quality),
                'Bedtime': str(bedtime),
                'Wake_Time': str(wake_time)
            }])
            st.session_state.sleep_log = pd.concat([st.session_state.sleep_log, new_entry], ignore_index=True)
            st.success(f"Logged {sleep_hours} hours of {sleep_quality.lower()} sleep for {date.today()}.")

    if not st.session_state.sleep_log.empty:
        # Sleep Analytics
        sleep_df = st.session_state.sleep_log.copy()
        sleep_df['Date'] = pd.to_datetime(sleep_df['Date'])
        
        # Sleep duration trend
        fig1 = px.line(sleep_df, x='Date', y='Sleep_Hours', 
                      title="Sleep Duration Trend",
                      labels={'Sleep_Hours': 'Hours of Sleep', 'Date': 'Date'})
        fig1.update_layout(height=300)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Sleep quality distribution
        col1, col2 = st.columns(2)
        with col1:
            quality_counts = sleep_df['Sleep_Quality'].value_counts()
            fig2 = px.pie(values=quality_counts.values, names=quality_counts.index, 
                         title="Sleep Quality Distribution")
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            avg_sleep = sleep_df['Sleep_Hours'].mean()
            st.metric("Average Sleep", f"{avg_sleep:.1f} hours")
            
            if len(sleep_df) > 1:
                sleep_trend = sleep_df['Sleep_Hours'].iloc[-1] - sleep_df['Sleep_Hours'].iloc[-2]
                st.metric("Sleep Trend", f"{sleep_trend:+.1f} hours", delta=f"{sleep_trend:+.1f}")

def display_workout_tracker():
    """Displays UI for logging workouts and showing workout analytics."""
    st.header("💪 Workout Tracker")
    
    with st.form("workout_form"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            workout_type = st.selectbox("Workout Type", ["Cardio", "Strength", "Flexibility", "Sports", "Other"])
        with col2:
            duration = st.number_input("Duration (minutes)", 5, 300, 60, 5)
        with col3:
            calories_burned = st.number_input("Calories Burned", 50, 1000, 300, 50)
        with col4:
            notes = st.text_input("Notes", placeholder="How did it feel?")
        
        submitted = st.form_submit_button("Log Workout")
        if submitted:
            new_entry = pd.DataFrame([{
                'Date': date.today(),
                'Workout_Type': str(workout_type),
                'Duration': int(duration),
                'Calories_Burned': int(calories_burned),
                'Notes': str(notes)
            }])
            st.session_state.workout_log = pd.concat([st.session_state.workout_log, new_entry], ignore_index=True)
            st.success(f"Logged {workout_type} workout: {duration} minutes, {calories_burned} calories burned.")

    if not st.session_state.workout_log.empty:
        # Workout Analytics
        workout_df = st.session_state.workout_log.copy()
        workout_df['Date'] = pd.to_datetime(workout_df['Date'])
        
        # Weekly workout summary
        weekly_workouts = workout_df[
            workout_df['Date'] >= (datetime.now() - timedelta(days=7)).date()
        ]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("This Week", len(weekly_workouts), "workouts")
        with col2:
            weekly_calories = weekly_workouts['Calories_Burned'].sum()
            st.metric("Calories Burned", f"{weekly_calories:,}", "this week")
        with col3:
            weekly_duration = weekly_workouts['Duration'].sum()
            st.metric("Total Time", f"{weekly_duration}", "minutes")
        
        # Workout type distribution
        type_counts = workout_df['Workout_Type'].value_counts()
        fig = px.bar(x=type_counts.index, y=type_counts.values,
                    title="Workout Type Distribution",
                    labels={'x': 'Workout Type', 'y': 'Count'})
        st.plotly_chart(fig, use_container_width=True)

def display_nutrition_tracker():
    """Displays UI for logging nutrition and showing nutrition analytics."""
    st.header("🍎 Nutrition Tracker")
    
    with st.form("nutrition_form"):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
        with col2:
            calories = st.number_input("Calories", 0, 2000, 500, 50)
        with col3:
            protein = st.number_input("Protein (g)", 0, 100, 20, 5)
        with col4:
            carbs = st.number_input("Carbs (g)", 0, 200, 50, 5)
        with col5:
            fat = st.number_input("Fat (g)", 0, 100, 15, 5)
        
        notes = st.text_input("Notes", placeholder="What did you eat?")
        
        submitted = st.form_submit_button("Log Meal")
        if submitted:
            new_entry = pd.DataFrame([{
                'Date': date.today(),
                'Meal': str(meal),
                'Calories': int(calories),
                'Protein': int(protein),
                'Carbs': int(carbs),
                'Fat': int(fat),
                'Notes': str(notes)
            }])
            st.session_state.nutrition_log = pd.concat([st.session_state.nutrition_log, new_entry], ignore_index=True)
            st.success(f"Logged {meal}: {calories} calories")

    if not st.session_state.nutrition_log.empty:
        # Nutrition Analytics
        nutrition_df = st.session_state.nutrition_log.copy()
        nutrition_df['Date'] = pd.to_datetime(nutrition_df['Date'])
        
        # Today's nutrition summary
        today_nutrition = nutrition_df[nutrition_df['Date'] == date.today()]
        
        if not today_nutrition.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Calories", f"{today_nutrition['Calories'].sum()}")
            with col2:
                st.metric("Protein", f"{today_nutrition['Protein'].sum()}g")
            with col3:
                st.metric("Carbs", f"{today_nutrition['Carbs'].sum()}g")
            with col4:
                st.metric("Fat", f"{today_nutrition['Fat'].sum()}g")
        
        # Weekly nutrition trend
        weekly_nutrition = nutrition_df[
            nutrition_df['Date'] >= (datetime.now() - timedelta(days=7)).date()
        ].groupby('Date').agg({
            'Calories': 'sum',
            'Protein': 'sum',
            'Carbs': 'sum',
            'Fat': 'sum'
        }).reset_index()
        
        fig = make_subplots(rows=2, cols=2, subplot_titles=('Calories', 'Protein', 'Carbs', 'Fat'))
        
        fig.add_trace(go.Scatter(x=weekly_nutrition['Date'], y=weekly_nutrition['Calories'], name='Calories'), row=1, col=1)
        fig.add_trace(go.Scatter(x=weekly_nutrition['Date'], y=weekly_nutrition['Protein'], name='Protein'), row=1, col=2)
        fig.add_trace(go.Scatter(x=weekly_nutrition['Date'], y=weekly_nutrition['Carbs'], name='Carbs'), row=2, col=1)
        fig.add_trace(go.Scatter(x=weekly_nutrition['Date'], y=weekly_nutrition['Fat'], name='Fat'), row=2, col=2)
        
        fig.update_layout(height=500, title_text="Weekly Nutrition Trends")
        st.plotly_chart(fig, use_container_width=True)

def display_progress_tracker():
    """Displays UI for logging weight and showing progress chart."""
    st.header("📈 Progress Tracker")
    
    # Ensure user_data exists and has weight with type safety
    if 'user_data' not in st.session_state or 'weight' not in st.session_state.user_data:
        st.error("Please complete your profile first.")
        return
    
    with st.form("progress_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            current_weight = st.session_state.user_data.get('weight', 70)
            # Ensure current_weight is a float for the number_input
            try:
                current_weight = float(current_weight)
            except (ValueError, TypeError):
                current_weight = 70.0
                
            new_weight = st.number_input(
                "Today's Weight (kg)", 
                min_value=30.0, 
                max_value=300.0, 
                value=current_weight, 
                step=0.1
            )
        with col2:
            body_fat = st.number_input("Body Fat %", 5.0, 50.0, 20.0, 0.5)
        with col3:
            muscle_mass = st.number_input("Muscle Mass (kg)", 20.0, 100.0, 50.0, 0.5)
        with col4:
            log_date = st.date_input("Date", value=date.today())
        
        submitted = st.form_submit_button("Log Progress")
        if submitted:
            # Validate the new weight entry with type safety
            try:
                new_weight = float(new_weight)
                body_fat = float(body_fat)
                muscle_mass = float(muscle_mass)
            except (ValueError, TypeError):
                st.error("Invalid values. Please enter valid numbers.")
                return
                
            if new_weight < 30.0 or new_weight > 300.0:
                st.error("Weight must be between 30 and 300 kg.")
                return
                
            new_entry = pd.DataFrame([{
                'Date': log_date, 
                'Weight': new_weight,
                'Body_Fat': body_fat,
                'Muscle_Mass': muscle_mass
            }])
            st.session_state.progress_log = pd.concat([st.session_state.progress_log, new_entry], ignore_index=True)
            st.success(f"Logged progress for {log_date}: Weight {new_weight:.1f}kg, Body Fat {body_fat:.1f}%, Muscle Mass {muscle_mass:.1f}kg")
            
            # Update current weight in user data
            st.session_state.user_data['weight'] = new_weight

    if not st.session_state.progress_log.empty:
        try:
            # Ensure Date column is properly formatted
            st.session_state.progress_log['Date'] = pd.to_datetime(st.session_state.progress_log['Date'])
            
            # Sort by date for proper chart display
            sorted_log = st.session_state.progress_log.sort_values('Date')
            
            # Create comprehensive progress charts
            fig = make_subplots(rows=2, cols=2, subplot_titles=('Weight Trend', 'Body Fat %', 'Muscle Mass', 'Body Composition'))
            
            # Weight trend
            fig.add_trace(go.Scatter(x=sorted_log['Date'], y=sorted_log['Weight'], 
                                   mode='lines+markers', name='Weight'), row=1, col=1)
            
            # Body fat trend
            fig.add_trace(go.Scatter(x=sorted_log['Date'], y=sorted_log['Body_Fat'], 
                                   mode='lines+markers', name='Body Fat %'), row=1, col=2)
            
            # Muscle mass trend
            fig.add_trace(go.Scatter(x=sorted_log['Date'], y=sorted_log['Muscle_Mass'], 
                                   mode='lines+markers', name='Muscle Mass'), row=2, col=1)
            
            # Body composition (pie chart for latest)
            if len(sorted_log) > 0:
                latest = sorted_log.iloc[-1]
                fat_mass = (latest['Weight'] * latest['Body_Fat'] / 100)
                muscle = latest['Muscle_Mass']
                other = latest['Weight'] - fat_mass - muscle
                
                fig.add_trace(go.Pie(values=[fat_mass, muscle, other], 
                                   labels=['Fat Mass', 'Muscle Mass', 'Other'], 
                                   name="Body Composition"), row=2, col=2)
            
            fig.update_layout(height=600, title_text="Comprehensive Progress Tracking")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show progress summary with type safety
            if len(sorted_log) > 1:
                try:
                    first_weight = float(sorted_log.iloc[0]['Weight'])
                    last_weight = float(sorted_log.iloc[-1]['Weight'])
                    weight_change = last_weight - first_weight
                    change_text = f"Gained {weight_change:.1f} kg" if weight_change > 0 else f"Lost {abs(weight_change):.1f} kg" if weight_change < 0 else "No change"
                    st.metric("Total Progress", change_text, delta=f"{weight_change:.1f} kg")
                except (ValueError, TypeError) as e:
                    st.error(f"Error calculating progress: {e}")
                
        except Exception as e:
            st.error(f"Error displaying progress chart: {e}")

def display_goals_settings():
    """Displays goal setting interface."""
    st.header("🎯 Goal Settings")
    
    with st.form("goals_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            target_weight = st.number_input("Target Weight (kg)", 30.0, 300.0, float(st.session_state.goals.get('target_weight', 65)), 0.5)
            target_sleep = st.number_input("Target Sleep (hours)", 6.0, 12.0, float(st.session_state.goals.get('target_sleep', 8)), 0.5)
        
        with col2:
            target_workouts = st.number_input("Target Weekly Workouts", 1, 7, int(st.session_state.goals.get('target_workouts', 4)))
            target_calories = st.number_input("Target Daily Calories", 1000, 5000, int(st.session_state.goals.get('target_calories', 2000)), 100)
        
        submitted = st.form_submit_button("Update Goals")
        if submitted:
            st.session_state.goals = {
                'target_weight': float(target_weight),
                'target_sleep': float(target_sleep),
                'target_workouts': int(target_workouts),
                'target_calories': int(target_calories)
            }
            st.success("Goals updated successfully!")

# --- Main App Layout ---

# Main header
st.markdown("""
<div class="main-header">
    <h1>🏃‍♂️ FitAI Pro</h1>
    <p>Your AI-powered fitness tracking companion</p>
</div>
""", unsafe_allow_html=True)

display_sidebar()

# Main content area
if st.session_state.plan_data:
    st.success("✅ Your personalized plan is ready! You can find it below.")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Dashboard", "🥗 Diet Plan", "💪 Gym Plan", "😴 Sleep", "💪 Workouts", "🍎 Nutrition", "📈 Progress"
    ])
    
    with tab1:
        display_dashboard()
    
    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        diet_plan = st.session_state.plan_data.get("diet_plan", "No diet plan generated.")
        if diet_plan and str(diet_plan) != "No diet plan generated.":
            st.markdown(str(diet_plan))
        else:
            st.warning("Diet plan not available. Please regenerate your plan.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        gym_plan = st.session_state.plan_data.get("gym_plan", "No gym/exercise plan generated.")
        if gym_plan and str(gym_plan) != "No gym/exercise plan generated.":
            st.markdown(str(gym_plan))
        else:
            st.warning("Gym plan not available. Please regenerate your plan.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        display_sleep_tracker()
    
    with tab5:
        display_workout_tracker()
    
    with tab6:
        display_nutrition_tracker()
    
    with tab7:
        display_progress_tracker()

else:
    # Show dashboard and other features even without AI plan
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "😴 Sleep", "💪 Workouts", "🍎 Nutrition", "📈 Progress", "🎯 Goals"
    ])
    
    with tab1:
        display_dashboard()
    
    with tab2:
        display_sleep_tracker()
    
    with tab3:
        display_workout_tracker()
    
    with tab4:
        display_nutrition_tracker()
    
    with tab5:
        display_progress_tracker()
    
    with tab6:
        display_goals_settings()

# Download functionality
if st.session_state.plan_data:
    with st.expander("📥 Download Your Plan"):
        diet_plan_text = st.session_state.plan_data.get('diet_plan', '')
        gym_plan_text = st.session_state.plan_data.get('gym_plan', '')
        
        # Ensure both texts are strings
        diet_plan_text = str(diet_plan_text) if diet_plan_text else ""
        gym_plan_text = str(gym_plan_text) if gym_plan_text else ""
        
        if diet_plan_text and gym_plan_text:
            full_plan_text = f"--- DIET PLAN ---\n\n{diet_plan_text}\n\n--- GYM/EXERCISE PLAN ---\n\n{gym_plan_text}"
            st.download_button(
                label="📥 Download Full Plan (.txt)",
                data=full_plan_text,
                file_name="ai_fitness_plan.txt",
                mime="text/plain"
            )
        else:
            st.warning("Cannot download plan - incomplete data available.")