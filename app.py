# --- File: app.py ---
import streamlit as st
import openai
from streamlit_chat import message
import os
import json
from dotenv import load_dotenv
# --- Load API Key (for local dev only) ---
load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# --- Constants ---
USER_FILE = "users.json"
COMPANY_FILE = "companies.json"

# --- Persistent Data Functions ---
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f)

def load_companies():
    if os.path.exists(COMPANY_FILE):
        with open(COMPANY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_companies(data):
    with open(COMPANY_FILE, "w") as f:
        json.dump(data, f)

# --- Load Users & Companies ---
users = load_users()
companies = load_companies()

# --- Session State Initialization ---
for key in ["chat_history", "interview_step", "interview_started", "owner_mode", "profile_created", "company_registered"]:
    if key not in st.session_state:
        st.session_state[key] = False

# --- Authentication ---
OWNER_EMAIL = "owner@example.com"
OWNER_PASS = "admin1112"

if not st.session_state.get("logged_in"):
    st.title("🔐 Login / Sign Up")
    st.write("## For New Users:")
    new_email = st.text_input("New Email")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Sign Up"):
        if new_email not in users:
            users[new_email] = {"password": new_pass}
            save_users(users)
            st.success("User registered successfully!")
        else:
            st.warning("User already exists.")

    st.write("---")
    st.write("## Existing Users / Owner Login:")
    login_email = st.text_input("Login Email")
    login_password = st.text_input("Login Password", type="password")

    if st.button("Login"):
        if login_email == OWNER_EMAIL and login_password == OWNER_PASS:
            st.session_state.logged_in = True
            st.session_state.owner_mode = True
            st.success("Logged in as Owner ✅")
        elif login_email in users and users[login_email]["password"] == login_password:
            st.session_state.logged_in = True
            st.session_state.owner_mode = False
            st.success("Logged in as User ✅")
        else:
            st.error("Invalid credentials")
    st.stop()

# --- Owner Tools ---
if st.session_state.owner_mode:
    st.sidebar.header("🛠️ Owner Tools")
    if st.sidebar.button("🗑️ Delete All User Accounts"):
        users = {}
        save_users(users)
        st.sidebar.success("✅ All user accounts deleted")
    if st.sidebar.button("🗑️ Delete All Company Records"):
        companies = {}
        save_companies(companies)
        st.sidebar.success("✅ All company records deleted")
    st.sidebar.markdown("### 📊 Analytics")
    st.sidebar.info(f"👤 Users: {len(users)} | 🏢 Companies: {len(companies)}")

# --- Profile Section ---
st.header("👤 Create Profile")
with st.form("profile_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", 18, 99)
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    state = st.text_input("State")
    city = st.text_input("City")
    domain = st.text_input("Domain (e.g., AI, Web Dev)")
    education = st.selectbox("Education Level", ["UG", "PG", "Diploma", "Other"])
    submitted = st.form_submit_button("Save Profile")
    if submitted:
        st.session_state.profile_created = True
        st.success("✅ Profile created successfully!")

# --- Company Registration ---
st.header("🏢 Company Registration")
with st.form("company_form"):
    c_name = st.text_input("Company Name")
    c_email = st.text_input("Company Email (for resume delivery)")
    c_loc = st.text_input("Location")
    c_branch = st.text_input("Branch (optional)")
    c_req = st.text_area("Hiring Requirements (keywords)")
    c_logo = st.file_uploader("Upload Logo (optional)", type=["png", "jpg", "jpeg"])
    reg_submit = st.form_submit_button("Register Company")
    if reg_submit:
        companies[c_name] = {
            "email": c_email, "location": c_loc, "branch": c_branch, "requirements": c_req
        }
        save_companies(companies)
        st.session_state.company_registered = True
        st.success("✅ Company Registered")

# --- Resume Upload ---
st.header("📄 Upload Resume")
resume = st.file_uploader("Upload your resume file", type=["pdf", "txt", "docx"])
if resume:
    st.success("✅ Resume uploaded successfully!")
    st.session_state.resume_uploaded = True

# --- Resume Matching Simulation ---
st.header("📍 Resume Matching")
if st.session_state.resume_uploaded and st.session_state.company_registered:
    selected = st.selectbox("Choose Company to Match Resume", list(companies.keys()))
    if st.button("🔍 Match Resume"):
        req = companies[selected]["requirements"].lower()
        if any(word in resume.name.lower() for word in req.split()):
            st.success(f"✅ Resume matched with {selected}")
        else:
            st.warning("⚠️ Resume did not match. Try training below.")

# --- Mock Interview ---
st.header("🎤 AI Mock Interview")
questions = [
    "Tell me about yourself.",
    "Why do you want this role?",
    "What challenges have you faced?",
    "Describe your project experience.",
    "Where do you see yourself in 5 years?"
]
if st.button("Start AI Interview"):
    st.session_state.interview_started = True
    st.session_state.interview_step = 0

if st.session_state.interview_started:
    if st.session_state.interview_step < len(questions):
        q = questions[st.session_state.interview_step]
        st.subheader(f"Question {st.session_state.interview_step+1}: {q}")
        ans = st.text_area("Answer here:")
        if st.button("Submit Answer"):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI HR giving feedback."},
                    {"role": "user", "content": ans}
                ]
            )
            st.success(response.choices[0].message.content)
            st.session_state.interview_step += 1
    else:
        st.success("🎉 Interview Complete")
        st.session_state.interview_started = False

# --- LAKS Chatbox ---
st.header("💬 LAKS - Your Career Assistant")
with st.form("laks_chat", clear_on_submit=True):
    user_input = st.text_input("Ask anything:")
    submit_chat = st.form_submit_button("Ask LAKS")
    if submit_chat and user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
        )
        reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.write(reply)
