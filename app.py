# --- File: app.py ---
import streamlit as st
import openai
from streamlit_chat import message
import os
import json
from dotenv import load_dotenv

# --- Load API Key (For Streamlit Cloud use secrets) ---
load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# --- Constants ---
USER_FILE = "users.json"
COMPANY_FILE = "companies.json"

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

# --- Session State Initialization ---
def init_session():
    keys = ["chat_history", "interview_step", "interview_started", "owner_mode",
            "logged_in", "user_email", "selected_company", "user_profile", "selected_level"]
    for key in keys:
        if key not in st.session_state:
            st.session_state[key] = None if key in ["user_email", "user_profile", "selected_company", "selected_level"] else False
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
        if st.button("Login"):
            if email == OWNER_EMAIL and password == OWNER_PASS:
                st.session_state.logged_in = True
                st.session_state.owner_mode = True
                st.success("✅ Logged in as Owner")
            elif email in users and users[email]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.owner_mode = False
                st.session_state.user_email = email
                st.session_state.user_profile = users[email]
                st.success("✅ Logged in as User")
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("Email (New User)")
        new_password = st.text_input("Password (New User)", type="password")
        if st.button("Register"):
            if new_email in users:
                st.warning("User already exists!")
            else:
                users[new_email] = {"password": new_password, "profile": {}, "resume": ""}
                save_json(users, USER_FILE)
                st.success("User registered! Now log in.")

    st.stop()

if not st.session_state.logged_in:
    auth_ui()

# --- Owner Panel ---
if st.session_state.owner_mode:
    st.sidebar.header("🛠️ Owner Tools")
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

    search_company = st.sidebar.text_input("Delete specific company (name)")
    if st.sidebar.button("Delete Company") and search_company in companies:
        companies.pop(search_company)
        save_json(companies, COMPANY_FILE)
        st.sidebar.success(f"Deleted {search_company}")

    st.subheader("📊 Platform Analytics")
    st.metric("Total Users", len(users))
    st.metric("Total Companies", len(companies))
    st.stop()

# --- User Interface ---
st.title("🤖 IntelliHire: AI-Powered Job Matcher")

# --- User Profile Setup ---
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

# --- Resume Upload ---
st.header("📄 Upload Resume")
uploaded = st.file_uploader("Upload your resume (PDF/DOCX)", type=["pdf", "docx"])
if uploaded:
    resume_text = uploaded.read().decode("utf-8", errors="ignore")
    users[st.session_state.user_email]["resume"] = resume_text
    save_json(users, USER_FILE)
    st.success("Resume uploaded and stored.")

# --- Company Registration ---
st.header("🏢 Company Registration")
with st.form("company_form"):
    cname = st.text_input("Company Name")
    branch = st.text_input("Branch (optional)")
    location = st.text_input("Location")
    email = st.text_input("Company Email (for resumes)")
    skills = st.text_area("Required Skills (comma-separated)")
    logo = st.file_uploader("Company Logo (optional)", type=["jpg", "jpeg", "png"])
    reg_submit = st.form_submit_button("Register Company")
    if reg_submit:
        companies[cname] = {"email": email, "skills": skills.split(","), "location": location, "branch": branch}
        save_json(companies, COMPANY_FILE)
        st.success(f"{cname} registered!")

# --- AI Interview Mode ---
st.header("🧠 AI Mock Interview")
level = st.selectbox("Select Interview Level", ["Easy", "Moderate", "Hard", "All"])
st.session_state.selected_level = level

match_found = False
for cname, cdata in companies.items():
    if any(skill.strip().lower() in users[st.session_state.user_email]["resume"].lower() for skill in cdata["skills"]):
        match_found = True
        st.session_state.selected_company = cname
        break

if not match_found:
    st.warning("No matching company found. You can still practice with any registered company.")
    st.session_state.selected_company = st.selectbox("Select a company to practice with:", list(companies.keys()))

# --- Ask AI Dynamically ---
if st.button("Start AI Interview"):
    company_req = companies[st.session_state.selected_company]["skills"]
    user_resume = users[st.session_state.user_email]["resume"]
    level_tag = f"Interview Difficulty: {level}"

    prompt = f"You are an AI HR from {st.session_state.selected_company}. Conduct a mock interview for a candidate whose resume includes: {user_resume}. Focus on skills: {company_req}. Ask {level.lower()} level questions."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": level_tag},
            {"role": "user", "content": prompt}
        ]
    )
    question = response.choices[0].message.content
    st.subheader("💬 AI HR Interviewer:")
    st.info(question)
    answer = st.text_area("🎙️ Your Answer (or respond via voice in future phase)")

    if st.button("Submit Answer"):
        feedback_prompt = f"This is the candidate's answer: {answer}. Provide feedback as an HR interviewer."
        feedback = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Give detailed feedback"},
                {"role": "user", "content": feedback_prompt}
            ]
        )
        st.success(feedback.choices[0].message.content)

# --- LAKS Chat ---
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
