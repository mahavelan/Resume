# --- File: app.py ---
import streamlit as st
import os
import json
from openai import OpenAI
from streamlit_chat import message
from dotenv import load_dotenv

# --- Load API Key ---
load_dotenv()
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))

# --- Constants ---
USER_FILE = "users.json"
COMPANY_FILE = "companies.json"

# --- Persistent Data Functions ---
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# --- Load Users & Companies ---
users = load_data(USER_FILE)
companies = load_data(COMPANY_FILE)

# --- Session State Initialization ---
for key, val in {
    "chat_history": [],
    "interview_step": 0,
    "interview_started": False,
    "owner_mode": False
}.items():
    st.session_state.setdefault(key, val)

# --- Owner Login ---
OWNER_EMAIL = "owner@example.com"
OWNER_PASS = "admin1112"

if not st.session_state.get("logged_in"):
    st.title("🔐 Secure Login")
    login_email = st.text_input("Email")
    login_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_email == OWNER_EMAIL and login_password == OWNER_PASS:
            st.session_state.logged_in = True
            st.session_state.owner_mode = True
            st.success("Logged in as Owner ✅")
        elif login_email in users and users[login_email]["password"] == login_password:
            st.session_state.logged_in = True
            st.session_state.owner_mode = False
            st.session_state.user_email = login_email
            st.success("Logged in as User ✅")
        else:
            st.error("Invalid credentials")
    st.stop()

# --- Owner Tools ---
if st.session_state.owner_mode:
    st.sidebar.header("🛠️ Owner Tools")

    if st.sidebar.button("Delete All User Accounts"):
        users = {}
        save_data(USER_FILE, users)
        st.sidebar.success("✅ All user accounts deleted!")

    del_user = st.sidebar.text_input("Delete user by email")
    if st.sidebar.button("Delete User"):
        if del_user in users:
            del users[del_user]
            save_data(USER_FILE, users)
            st.sidebar.success(f"User '{del_user}' deleted.")
        else:
            st.sidebar.warning("User not found")

    del_company = st.sidebar.text_input("Delete company by name")
    if st.sidebar.button("Delete Company"):
        if del_company in companies:
            del companies[del_company]
            save_data(COMPANY_FILE, companies)
            st.sidebar.success(f"Company '{del_company}' deleted.")
        else:
            st.sidebar.warning("Company not found")

# --- Sidebar: Avatar Upload ---
with st.sidebar:
    st.image("https://i.imgur.com/AvU0i8I.png", caption="AI HR Avatar", width=200)
    st.markdown("**Upload your own AI interviewer image:**")
    avatar = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if avatar:
        st.image(avatar, width=200)

# --- MAIN INTERFACE ---
st.set_page_config(page_title="INTELLIHIRE AI Interview + LAKS", layout="wide")
st.title("🤖 INTELLIHIRE AI Interview + LAKS")

# --- Section 1: AI Video Interview Experience (Mock Session) ---
st.header("🎥 AI Interview Session")
st.markdown("Simulating a modern AI-led interview experience with audio/chat support.")

questions = [
    "Tell me about yourself.",
    "What are your strengths and weaknesses?",
    "Why do you want to join our company?",
    "Describe a challenge you've overcome.",
    "Where do you see yourself in 5 years?"
]

if not st.session_state.interview_started:
    if st.button("🎬 Start AI Video Interview"):
        st.session_state.interview_started = True
        st.session_state.interview_step = 0

if st.session_state.interview_started:
    if st.session_state.interview_step < len(questions):
        current_q = questions[st.session_state.interview_step]
        st.subheader(f"AI Asks: {current_q}")
        st.markdown("📢 *AI reads out loud...* (Simulated Audio)")

        user_ans = st.text_area("🎤 Your Answer (You can also speak during deployment with mic integration)")

        if st.button("Submit Answer"):
            with st.spinner("AI is analyzing your answer..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You're an AI HR giving feedback on interview answers."},
                        {"role": "user", "content": f"Candidate answer: {user_ans}"}
                    ]
                )
                st.success(response.choices[0].message.content)
            st.session_state.interview_step += 1
    else:
        st.success("🎉 Interview Completed!")
        st.session_state.interview_started = False

# --- Section 2: LAKS Educational Chatbot ---
st.header("💬 LAKS - Smart Learning Chatbot")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask LAKS anything academic or job-related:")
    submitted = st.form_submit_button("Ask")

if submitted and user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("LAKS is thinking..."):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
        )
        reply = response.choices[0].message.content
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

for msg in st.session_state.chat_history:
    message(msg["content"], is_user=(msg["role"] == "user"))
