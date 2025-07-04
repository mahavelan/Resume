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

# --- Persistent User Data Functions ---
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f)

# --- Load Users Before Login ---
users = load_users()

# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_step" not in st.session_state:
    st.session_state.interview_step = 0
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "owner_mode" not in st.session_state:
    st.session_state.owner_mode = False

# --- Owner Login ---
OWNER_EMAIL = "owner@example.com"
OWNER_PASS = "admin1112"

if not st.session_state.get("logged_in"):
    st.set_page_config(page_title="INTELLIHIRE Login", layout="wide")
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
            st.success("Logged in as User ✅")
        else:
            st.error("Invalid credentials")
    st.stop()

# --- Owner Tools ---
if st.session_state.owner_mode:
    st.sidebar.header("🛠️ Owner Tools")
    if st.sidebar.button("Delete All User Accounts"):
        users = {}
        save_users(users)
        st.sidebar.success("✅ All user accounts deleted!")

# --- Sidebar: Avatar Upload ---
with st.sidebar:
    st.image("https://i.imgur.com/AvU0i8I.png", caption="AI HR Avatar", width=200)
    st.markdown("**Upload your own AI interviewer image:**")
    avatar = st.file_uploader("Upload Avatar", type=["png", "jpg", "jpeg"])
    if avatar:
        st.image(avatar, width=200)

# --- MAIN INTERFACE ---
st.set_page_config(page_title="INTELLIHIRE AI Interview + LAKS", layout="wide")
st.title("🤖 INTELLIHIRE AI Interview + LAKS")

# --- Section 1: AI Mock Interview ---
st.header("🎤 AI Mock Interview")

questions = [
    "Tell me about yourself.",
    "What are your strengths and weaknesses?",
    "Why do you want to join our company?",
    "Describe a challenge you've overcome.",
    "Where do you see yourself in 5 years?"
]

if not st.session_state.interview_started:
    if st.button("Start Practice Interview"):
        st.session_state.interview_started = True
        st.session_state.interview_step = 0

if st.session_state.interview_started:
    if st.session_state.interview_step < len(questions):
        current_q = questions[st.session_state.interview_step]
        st.subheader(f"Question {st.session_state.interview_step+1}: {current_q}")
        user_ans = st.text_area("Your Answer (type here):")

        if st.button("Submit Answer"):
            with st.spinner("Analyzing answer..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You're an AI HR giving feedback on interview answers."},
                        {"role": "user", "content": f"My answer: {user_ans}\nGive me feedback."}
                    ]
                )
                st.success(response.choices[0].message.content)
            st.session_state.interview_step += 1
    else:
        st.success("Interview complete! 🎉")
        st.session_state.interview_started = False

# --- Section 2: LAKS Chatbot ---
st.header("💬 LAKS - Study Support Chat")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask me anything academic or job-related:")
    submitted = st.form_submit_button("Ask LAKS")

if submitted and user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
        )
        reply = response.choices[0].message.content
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

# --- Display Chat History ---
for msg in st.session_state.chat_history:
    message(msg["content"], is_user=(msg["role"] == "user"))
