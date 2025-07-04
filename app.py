import streamlit as st
import openai
from streamlit_chat import message

# --- Setup ---
st.set_page_config(page_title="AI Interview & LAKS Chat", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]  # or use st.text_input() securely

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_step" not in st.session_state:
    st.session_state.interview_step = 0
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

# --- Sidebar: Avatar Upload ---
with st.sidebar:
    st.image("https://i.imgur.com/AvU0i8I.png", caption="AI HR Avatar", width=200)
    st.markdown("**Upload your own AI interviewer image:**")
    avatar = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if avatar:
        st.image(avatar, width=200)

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
    current_q = questions[st.session_state.interview_step]
    st.subheader(f"Question {st.session_state.interview_step+1}: {current_q}")
    user_ans = st.text_area("Your Answer (type here):")

    if st.button("Submit Answer"):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're an AI HR giving feedback on interview answers."},
                {"role": "user", "content": f"My answer: {user_ans}\nGive me feedback."}
            ]
        )
        st.success(response.choices[0].message.content)
        st.session_state.interview_step += 1
        if st.session_state.interview_step >= len(questions):
            st.session_state.interview_started = False
            st.success("Interview complete! 🎉")

# --- Section 2: LAKS Educational Chatbot ---
st.header("💬 LAKS - Study Support Chat")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask me anything academic or job-related:")
    submitted = st.form_submit_button("Ask LAKS")

if submitted and user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
    )
    reply = response.choices[0].message.content
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

# --- Show Chat History ---
for msg in st.session_state.chat_history:
    message(msg["content"], is_user=(msg["role"] == "user"))
