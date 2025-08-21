🤖 AI Fitness Instructor
A personalized, AI-powered diet and fitness planner built with Streamlit and Google's Gemini API. This interactive web application acts as a virtual fitness coach, generating custom health plans based on user-specific data and goals.

➡️ View Live Demo 👈 https://aifitnessagent-jcfaomnyg7xcc2xas5m85f.streamlit.app/

(Pro Tip: Take a screenshot or record a short GIF of your app and replace the link above to showcase your project visually.)

✨ Key Features
👤 Personalized Profiles: Users can input their age, gender, height, weight, and medical conditions to create a unique health profile.

🎯 Goal-Oriented Plans: Whether the goal is weight loss, muscle gain, or weight maintenance, the AI tailors the plan accordingly.

🥗 Custom Diet Plans: Generates detailed daily meal plans with calorie/macro estimates, meal options, and healthy eating principles.

💪 Structured Workout Routines: Creates weekly gym schedules with specific exercises, sets, reps, rest times, and clear instructions on proper form.

📈 Progress Tracking: A built-in tracker allows users to log their daily weight and visualize their progress over time with an interactive chart.

🤖 Powered by Gemini: Leverages Google's state-of-the-art Gemini Pro model to provide knowledgeable, encouraging, and human-like advice.

🌐 Interactive UI: A clean, user-friendly interface built with Streamlit, making it easy for anyone to generate and view their health plan.

⚙️ How It Works
The application follows a simple yet powerful workflow:

Data Input: The user provides their personal health metrics and fitness goals via an intuitive sidebar form.

Secure API Call: The user's data is compiled into a detailed prompt, which is then sent to the Gemini API endpoint. The API key is securely accessed from Streamlit's secrets management, never exposing it in the front-end code.

AI-Powered Generation: The Gemini model processes the prompt and generates a comprehensive plan in a structured JSON format, containing separate keys for the diet and gym plans.

Dynamic Display: The application parses the JSON response and dynamically displays the diet and workout plans in organized tabs.

Data Persistence: User profile data and progress logs are stored in the Streamlit session state, ensuring a smooth and persistent experience during a single session.

🛠️ Tech Stack
Frontend: Streamlit

AI Model: Google Gemini Pro

Data Handling: Pandas

Charting: Altair

API Communication: Requests

Deployment: Streamlit Community Cloud

🚀 Getting Started Locally
To run this project on your own machine, follow these steps:

1. Clone the Repository
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

2. Install Dependencies
Create and activate a virtual environment, then install the required packages.

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install packages
pip install -r requirements.txt

3. Set Up API Key
The application is designed to use Streamlit's secrets management. For local development, create a file at ~/.streamlit/secrets.toml (or .streamlit/secrets.toml in your project root) and add your API key:

# .streamlit/secrets.toml
GEMINI_API_KEY = "YOUR_API_KEY_HERE"

4. Run the App
streamlit run app.py

Open your web browser and navigate to http://localhost:8501
