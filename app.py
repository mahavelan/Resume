# --- File: app.py ---
import streamlit as st
import openai
from streamlit_chat import message
import os
import json
import time
from dotenv import load_dotenv

# --- Load API Key (For Streamlit Cloud use secrets) ---
load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

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
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        user_type = st.selectbox("Login as", ["User", "Company", "Owner"])

        if st.button("Login"):
            if user_type == "Owner" and email == OWNER_EMAIL and password == OWNER_PASS:
                st.session_state.logged_in = True
                st.session_state.owner_mode = True
                st.session_state.user_type = "owner"
                st.success("✅ Logged in as Owner")
                st.experimental_rerun()
            elif user_type == "User" and email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.owner_mode = False
                st.session_state.user_email = email
                st.session_state.user_profile = users[email].get("profile", {})
                st.session_state.user_type = "user"
                st.success("✅ Logged in as User")
                st.experimental_rerun()
            elif user_type == "Company" and email in companies and companies[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.owner_mode = False
                st.session_state.user_email = email
                st.session_state.user_profile = companies[email]
                st.session_state.user_type = "company"
                st.success("✅ Logged in as Company")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("Email (New Account)")
        new_password = st.text_input("Password (New Account)", type="password")
        new_type = st.selectbox("Register as", ["User", "Company"])
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
                    companies[new_email] = {"password": new_password, "skills": [], "location": "", "branch": ""}
                    save_json(companies, COMPANY_FILE)
                    st.success("Company registered! Now log in.")

if not st.session_state.logged_in:
    auth_ui()
    st.stop()

# --- Selection UI for Features ---
st.title("🤖 IntelliHire Dashboard")
choice = st.selectbox("Choose a feature", ["Home", "Create Profile", "Upload Resume", "Interview Dashboard", "AI Training", "Ask LAKS"])

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

# --- User Feature Handling ---
if st.session_state.user_type == "user":
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
                profile = {"name": name, "age": age, "phone": phone, "state": state, "city": city,
                           "domain": domain, "education": edu}
                users[st.session_state.user_email]["profile"] = profile
                st.session_state.user_profile = profile
                save_json(users, USER_FILE)
                st.success("Profile saved!")

    elif choice == "Upload Resume":
        st.header("📄 Upload Resume")
        uploaded = st.file_uploader("Upload your resume (PDF/DOCX)", type=["pdf", "docx"])
        if uploaded:
            resume_text = uploaded.read().decode("utf-8", errors="ignore")
            users[st.session_state.user_email]["resume"] = resume_text
            save_json(users, USER_FILE)

            matched = []
            for cname, cdata in companies.items():
                if any(skill.strip().lower() in resume_text.lower() for skill in cdata["skills"]):
                    matched.append(cname)
                    if st.session_state.user_email not in schedules:
                        schedules[st.session_state.user_email] = {}
                    schedules[st.session_state.user_email][cname] = {
                        "status": "selected",
                        "date": "2025-07-10",
                        "time": "10:00 AM",
                        "mode": "Online"
                    }
                else:
                    if st.session_state.user_email not in schedules:
                        schedules[st.session_state.user_email] = {}
                    feedback_prompt = f"Analyze this resume and provide reason why it may be rejected: {resume_text}"
                    feedback = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "system", "content": "You are an HR expert."},
                                  {"role": "user", "content": feedback_prompt}]
                    )
                    schedules[st.session_state.user_email][cname] = {
                        "status": "rejected",
                        "feedback": feedback.choices[0].message.content
                    }
            save_json(schedules, INTERVIEW_SCHEDULE_FILE)

            if matched:
                st.success("🎯 Resume matches with the following companies:")
                for c in matched:
                    st.write(f"✅ {c}")
            else:
                st.warning("No matching companies found.")

    elif choice == "Interview Dashboard":
        st.header("📅 Interview Dashboard")
        if st.session_state.user_email in schedules:
            for comp, data in schedules[st.session_state.user_email].items():
                st.write(f"**{comp}**")
                if data["status"] == "selected":
                    st.success(f"Interview on {data['date']} at {data['time']} ({data['mode']})")
                else:
                    st.error("Resume rejected")
                    st.write("Feedback:", data.get("feedback", "Not provided"))
                    if st.button(f"Suggest Resume Fix for {comp}"):
                        fix_prompt = f"Rewrite and improve this resume to match {comp} requirements: {resume_text}"
                        fix = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[{"role": "user", "content": fix_prompt}]
                        )
                        st.write("Suggested Resume:")
                        st.code(fix.choices[0].message.content)

    elif choice == "AI Training":
        st.header("🎥 AI Video Mock Interview")
        level = st.selectbox("Select Interview Level", ["Easy", "Moderate", "Hard", "All"])
        if st.button("Start AI Mock Interview"):
            company_req = [s for c in companies.values() for s in c["skills"]]
            resume = users[st.session_state.user_email].get("resume", "")
            prompt = f"Conduct a {level.lower()} level technical interview based on resume: {resume}. Required skills: {company_req}."
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a virtual HR conducting a technical interview."},
                    {"role": "user", "content": prompt}
                ]
            )
            question = response.choices[0].message.content
            st.subheader("🗣️ AI Interview Question")
            st.info(question)
            answer = st.text_area("🎤 Your Answer (speak or type)")
            if st.button("Submit Answer"):
                if not answer.strip():
                    st.warning("No answer detected. Showing answer in 10 seconds...")
                    time.sleep(10)
                    model_answer_prompt = f"Provide the best answer to: {question}"
                    model_answer = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": model_answer_prompt}]
                    )
                    st.write("Suggested Answer:")
                    st.success(model_answer.choices[0].message.content)
                else:
                    feedback_prompt = f"Provide detailed feedback to this candidate answer: {answer}"
                    feedback = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You're a senior HR giving constructive feedback."},
                            {"role": "user", "content": feedback_prompt}
                        ]
                    )
                    st.success("Feedback:")
                    st.write(feedback.choices[0].message.content)

    elif choice == "Ask LAKS":
        st.header("📚 Ask LAKS Anything")
        with st.form("laks_chat", clear_on_submit=True):
            user_input = st.text_input("Ask about careers, coding, jobs...")
            send = st.form_submit_button("Ask LAKS")
        if send and user_input:
            st.session_state.chat_history = st.session_state.chat_history or []
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            reply = openai.ChatCompletion.create(
                model="gpt-4",
                messages=st.session_state.chat_history
            )
            response = reply.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            message(response, is_user=False)

# --- History Management ---
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
