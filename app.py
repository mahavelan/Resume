# --- File: app.py ---
import streamlit as st
import openai
from streamlit_chat import message
import os
import json
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import tempfile

# --- Load API Key ---
load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
# --- Load API key securely ---

# --- Constants ---
USER_FILE = "users.json"
COMPANY_FILE = "companies.json"
INTERVIEW_SCHEDULE_FILE = "interview_schedules.json"

# --- Utility Functions ---
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

users = load_json(USER_FILE)
companies = load_json(COMPANY_FILE)
schedules = load_json(INTERVIEW_SCHEDULE_FILE)

# --- Session State Initialization ---
def init_session():
    keys = ["chat_history", "interview_step", "interview_started", "owner_mode",
            "logged_in", "user_email", "selected_company", "user_profile", "selected_level", "user_type"]
    for key in keys:
        if key not in st.session_state:
            st.session_state[key] = None if key in ["user_email", "user_profile", "selected_company", "selected_level", "user_type"] else False
init_session()

# --- Owner Constants ---
OWNER_EMAIL = "owner@example.com"
OWNER_PASS = "admin123"

# --- Authentication ---
def auth_ui():
    st.title("🔐 Welcome to IntelliHire")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        user_type = st.selectbox("Login as", ["User", "Company", "Owner"], key="login_type")

        if st.button("Login"):
            if user_type == "Owner" and email == OWNER_EMAIL and password == OWNER_PASS:
                st.session_state.logged_in = True
                st.session_state.owner_mode = True
                st.session_state.user_type = "owner"
                st.success("✅ Logged in as Owner")
                st.rerun()
            elif user_type == "User" and email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.owner_mode = False
                st.session_state.user_email = email
                st.session_state.user_profile = users[email].get("profile", {})
                st.session_state.user_type = "user"
                st.success("✅ Logged in as User")
                st.rerun()
            elif user_type == "Company" and email in companies and companies[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.owner_mode = False
                st.session_state.user_email = email
                st.session_state.user_profile = companies[email]
                st.session_state.user_type = "company"
                st.success("✅ Logged in as Company")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("Email (New Account)", key="reg_email")
        new_password = st.text_input("Password (New Account)", type="password", key="reg_password")
        new_type = st.selectbox("Register as", ["User", "Company"], key="reg_type")
        if st.button("Register"):
            if new_type == "User":
                if new_email in users:
                    st.warning("User already exists!")
                else:
                    users[new_email] = {"password": new_password, "profile": {}, "resume": ""}
                    save_json(users, USER_FILE)
                    st.success("User registered! Now log in.")
            elif new_type == "Company":
                if new_email in companies:
                    st.warning("Company already exists!")
                else:
                    companies[new_email] = {"password": new_password, "skills": [], "location": "", "branch": "", "name": ""}
                    save_json(companies, COMPANY_FILE)
                    st.success("Company registered! Now log in.")

if not st.session_state.logged_in:
    auth_ui()
    st.stop()

# --- Selection UI for Features ---
st.title("🤖 IntelliHire Dashboard")
if st.session_state.user_type == "user":
    choice = st.selectbox("Choose a feature", ["Create Profile", "Upload Resume", "Interview Dashboard", "AI Training", "Ask LAKS"], key="main_user_choice")
elif st.session_state.user_type == "company":
    choice = st.selectbox("Company Panel", ["Register Details", "View Applications"], key="main_company_choice")
else:
    choice = "Home"

# --- Owner Panel ---
if st.session_state.user_type == "owner":
    st.title("🛠️ Owner Dashboard")
    st.sidebar.header("Owner Tools")

    st.metric("Total Users", len(users))
    st.metric("Total Companies", len(companies))
    st.metric("Scheduled Interviews", len(schedules))

    for email, details in users.items():
        st.subheader(f"User: {email}")
        st.json(details)

    for cname, cdetails in companies.items():
        st.subheader(f"Company: {cname}")
        st.json(cdetails)

    if st.sidebar.button("Delete All Users"):
        users.clear()
        save_json(users, USER_FILE)
        st.sidebar.success("All users deleted")

    if st.sidebar.button("Delete All Companies"):
        companies.clear()
        save_json(companies, COMPANY_FILE)
        st.sidebar.success("All companies deleted")

    search_user = st.sidebar.text_input("Delete specific user (email)")
    if st.sidebar.button("Delete User") and search_user in users:
        users.pop(search_user)
        save_json(users, USER_FILE)
        st.sidebar.success(f"Deleted {search_user}")

    search_company = st.sidebar.text_input("Delete specific company (email)")
    if st.sidebar.button("Delete Company") and search_company in companies:
        companies.pop(search_company)
        save_json(companies, COMPANY_FILE)
        st.sidebar.success(f"Deleted {search_company}")

    st.stop()

# --- Placeholder for Full Feature Set ---
# Continue adding AI Interview, Resume Upload, Profile Creation, etc. features here.
# This scaffolding avoids duplication bugs and supports modular development.


# --- Company Panel ---
if st.session_state.user_type == "company":
    if choice == "Register Details":
        st.header("🏢 Company Registration")
        with st.form("company_form"):
            cname = st.text_input("Company Name")
            branch = st.text_input("Branch")
            location = st.text_input("Location")
            skills = st.text_area("Required Skills (comma-separated)")
            submitted = st.form_submit_button("Update Company Info")
            if submitted:
                companies[st.session_state.user_email].update({
                    "skills": [s.strip() for s in skills.split(",")],
                    "location": location,
                    "branch": branch,
                    "name": cname
                })
                save_json(companies, COMPANY_FILE)
                st.success("Company details updated.")

    elif choice == "View Applications":
        st.header("📂 Candidate Applications")
        found = False
        for user, applications in schedules.items():
            if st.session_state.user_email in applications:
                found = True
                details = users[user].get("profile", {})
                st.write(f"**{user}**: {details.get('name', 'N/A')} - {applications[st.session_state.user_email]['status']}")
                if applications[st.session_state.user_email]['status'] == "selected":
                    st.write(f"Scheduled: {applications[st.session_state.user_email]['date']} at {applications[st.session_state.user_email]['time']}")
                else:
                    st.write("Feedback:", applications[st.session_state.user_email].get("feedback", "-"))
        if not found:
            st.warning("No applications yet.")
#----------user panel---------#
if st.session_state.user_type == "user":

    choice = st.selectbox("Choose a feature", [..], key="user_panel_choice")

    if choice == "Create Profile":
        st.header("👤 Create Your Profile")
        with st.form("profile_form"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=18, max_value=60)
            phone = st.text_input("Phone")
            state = st.text_input("State")
            city = st.text_input("City")
            domain = st.text_input("Domain (e.g., AI, Data Science)")
            edu = st.selectbox("Education", ["UG", "PG", "Diploma", "Other"])
            submitted = st.form_submit_button("Save Profile")
            if submitted:
                profile = {
                    "name": name, "age": age, "phone": phone,
                    "state": state, "city": city, "domain": domain, "education": edu
                }
                users[st.session_state.user_email]["profile"] = profile
                st.session_state.user_profile = profile
                save_json(users, USER_FILE)
                st.success("Profile saved!")

    elif choice == "Upload Resume":
        st.header("📄 Upload Resume")
        uploaded = st.file_uploader("Upload your resume (PDF/DOCX)", type=["pdf", "docx"], key="resume_upload")
        if uploaded:
            resume_text = uploaded.read().decode("utf-8", errors="ignore")
            users[st.session_state.user_email]["resume"] = resume_text
            save_json(users, USER_FILE)
            st.success("Resume uploaded and stored.")

    elif choice == "Interview Dashboard":
        st.header("🧠 AI Mock Interview")
        level = st.selectbox("Select Interview Level", ["Easy", "Moderate", "Hard", "All"])
        st.session_state.selected_level = level
        matching_companies = []
        resume_text = users[st.session_state.user_email].get("resume", "")

        for cname, cdata in companies.items():
            if resume_text and any(skill.strip().lower() in resume_text.lower() for skill in cdata["skills"]):
                matching_companies.append(cname)

        if matching_companies:
            st.session_state.selected_company = st.selectbox("Select matching company", matching_companies)
        else:
            st.warning("No matching company found. You can still practice with any registered company.")
            st.session_state.selected_company = st.selectbox("Select a company to practice with:", list(companies.keys()))

        if st.button("Start AI Interview"):
            company_req = companies[st.session_state.selected_company]["skills"]
            user_resume = users[st.session_state.user_email]["resume"]
            level_tag = f"Interview Difficulty: {level}"

            prompt = f"You are an AI HR from {st.session_state.selected_company}. Conduct a mock interview for a candidate whose resume includes: {user_resume}. Focus on skills: {company_req}. Ask {level.lower()} level questions."

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": level_tag},
                    {"role": "user", "content": prompt}
                ]
            )
            question = response.choices[0].message.content
            st.subheader("💬 AI HR Interviewer:")
            st.info(question)
            answer = st.text_area("🎧 Your Answer")

            if st.button("Submit Answer"):
                feedback_prompt = f"This is the candidate's answer: {answer}. Provide feedback as an HR interviewer."
                feedback = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Give detailed feedback"},
                        {"role": "user", "content": feedback_prompt}
                    ]
                )
                st.success(feedback.choices[0].message.content)

    elif choice == "AI Training":
        st.header("🎓 AI Training Session (Simulated Video Call)")
        st.info("Simulated video/audio-only interface. Mic stays active. You can chat with AI in the IntelliHire Chatbox.")

        st.subheader("🎙️ Speak to AI Trainer")
        audio_data = mic_recorder(start_prompt="🎙️ Click to Start Speaking", stop_prompt="⏹️ Stop", key="mic")

        if audio_data:
            raw_bytes = io.BytesIO(audio_data["bytes"])
            try:
                audio_segment = AudioSegment.from_file(raw_bytes)
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio = recognizer.record(source)

                try:
                    text_query = recognizer.recognize_google(audio)
                    st.success(f"🚣️ You said: {text_query}")

                    st.session_state.chat_history = st.session_state.get("chat_history", [])
                    st.session_state.chat_history.append({"role": "user", "content": text_query})

                    reply = openai.chat.completions.create(
                        model="gpt-4",
                        messages=st.session_state.chat_history
                    )
                    response = reply.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    message(response, is_user=False)

                except sr.UnknownValueError:
                    st.warning("Sorry, could not understand your speech.")
                except sr.RequestError as e:
                    st.error(f"Speech recognition failed: {e}")

            except Exception as e:
                st.error(f"Audio conversion failed: {e}")

        with st.expander("📨 IntelliHire Private Chat"):
            with st.form("ai_training_chat", clear_on_submit=True):
                query = st.text_input("Ask AI Trainer something...")
                submit = st.form_submit_button("Send")
            if submit and query:
                st.session_state.chat_history = st.session_state.get("chat_history", [])
                st.session_state.chat_history.append({"role": "user", "content": query})
                reply = openai.chat.completions.create(
                    model="gpt-4",
                    messages=st.session_state.chat_history
                )
                response = reply.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                message(response, is_user=False)

    elif choice == "Ask LAKS":
        st.header("📚 Ask LAKS Anything")
        with st.form("laks_chat", clear_on_submit=True):
            user_input = st.text_input("Ask about careers, coding, jobs...")
            send = st.form_submit_button("Ask LAKS")
        if send and user_input:
            st.session_state.chat_history = st.session_state.get("chat_history", [])
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            reply = openai.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.chat_history
            )
            response = reply.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            message(response, is_user=False)

    elif choice == "ATS Resume Fix":
        st.header("🛠️ Resume Fix Based on Company Feedback")
        email = st.session_state.user_email
        resume = users[email].get("resume", "")
        feedbacks = []
        for company, result in schedules.get(email, {}).items():
            if result.get("status") == "rejected" and result.get("feedback"):
                feedbacks.append((company, result["feedback"]))

        if not feedbacks:
            st.info("No rejected resumes with feedback found.")
        else:
            for company, feedback in feedbacks:
                st.subheader(f"Feedback from {company}:")
                st.warning(feedback)
                with st.expander(f"📝 View ATS Resume Fix Suggestion for {company}"):
                    prompt = f"Candidate resume: {resume}\nCompany feedback: {feedback}\nUpdate the resume content to address the feedback and improve alignment."
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are an expert resume editor."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        improved_resume = response.choices[0].message.content
                        st.text_area("🔧 Modified Resume Suggestion", value=improved_resume, height=300)
                    except Exception as e:
                        st.error(f"OpenAI error: {e}")

    if st.button("Clear Chat History"):
        st.session_state.chat_history = []



