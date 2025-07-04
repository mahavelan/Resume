# --- Streamlit Resume-Based AI HR App ---
import streamlit as st
import re
import os
import json
from datetime import datetime
from PyPDF2 import PdfReader
from docx import Document

# --- Constants ---
USER_FILE = "users.json"

# --- Persistent User Data Functions ---
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users_data):
    with open(USER_FILE, "w") as f:
        json.dump(users_data, f)

users = load_users()
companies = {}
resumes = {}
jobs = {
    "CompanyX": ["Python", "Machine Learning", "Communication"],
    "TechCorp": ["Java", "Spring", "REST API"],
}

st.set_page_config(page_title="INTELLIHIRE", layout="wide")

# --- Helper Functions ---
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_skills(text):
    skills = re.findall(r"(?i)\b(Python|Java|SQL|Excel|Machine Learning|AI|Spring|REST API|Communication|Leadership|Django)\b", text)
    return list(set(skills))

def match_jobs(user_skills):
    matched = []
    for company, reqs in jobs.items():
        if any(skill in user_skills for skill in reqs):
            matched.append(company)
    return matched

# --- Initialize Session State ---
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- Home Page ---
if st.session_state["page"] == "home":
    st.image("Tech Recruitment Service Logo INTELLIHIRE.png", width=200)
    st.title("Welcome to INTELLIHIRE")

    auth_choice = st.radio("Select Option:", ["Login", "Sign Up", "Forgot Password"])

    if auth_choice == "Login":
        st.subheader("🔐 Login with Email")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if login_email in users and users[login_email]["password"] == login_password:
                st.success("Login successful!")
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = login_email
                st.session_state["page"] = "dashboard"
            else:
                st.error("Invalid email or password.")

    elif auth_choice == "Sign Up":
        st.subheader("📝 Create New Account")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pass")

        if st.button("Sign Up"):
            if new_email in users:
                st.warning("Email already exists. Please log in.")
            else:
                users[new_email] = {"username": new_username, "password": new_password}
                save_users(users)
                st.success("Sign-up successful! Please log in now.")

    elif auth_choice == "Forgot Password":
        st.subheader("🔑 Reset Password")
        forgot_email = st.text_input("Enter your email")
        new_pass = st.text_input("Enter new password", type="password")
        if st.button("Reset"):
            if forgot_email in users:
                users[forgot_email]["password"] = new_pass
                save_users(users)
                st.success("Password updated successfully.")
            else:
                st.error("Email not found.")

# Auto-login if already authenticated
if st.session_state.get("logged_in") and st.session_state["page"] == "home":
    st.session_state["page"] = "dashboard"
    st.experimental_rerun()

# --- Dashboard ---
elif st.session_state["page"] == "dashboard":
    st.header("Dashboard")
    option = st.radio("Select Role:", ["User Profile", "Company Registration"])

    if option == "User Profile":
        st.subheader("Create Profile")
        name = st.text_input("Name")
        dob = st.date_input("Date of Birth")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        email = st.text_input("Email ID", value=st.session_state.get("user_email", ""))
        address = st.text_input("Address")
        city = st.text_input("City")
        state = st.text_input("State")
        phone = st.text_input("Phone Number")
        st.success("Profile Created")

    elif option == "Company Registration":
        st.subheader("Company Registration")
        cname = st.text_input("Company Name")
        cloc = st.text_input("Company Location")
        branches = st.text_area("Branches (if any)")
        photos = st.file_uploader("Upload Photos", accept_multiple_files=True)
        st.success("Company Registered")

    st.markdown("---")
    st.subheader("Upload Resume")
    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

    if uploaded_file:
        file_type = uploaded_file.type
        if "pdf" in file_type:
            text = extract_text_from_pdf(uploaded_file)
        else:
            text = extract_text_from_docx(uploaded_file)

        skills = extract_skills(text)
        st.write("Extracted Skills:", skills)
        matched_companies = match_jobs(skills)

        if matched_companies:
            st.success(f"Resume matched with: {', '.join(matched_companies)}")
            st.info("Your resume has been sent to the matched companies. Await interview call.")
        else:
            st.warning("No company match found. Proceeding to AI training...")
            st.session_state["page"] = "training"
            st.experimental_rerun()

# --- AI Training Page ---
elif st.session_state["page"] == "training":
    st.header("AI-Based Training")
    st.image("https://i.imgur.com/AvU0i8I.png", width=100)
    st.write("AI HR: Tell me about yourself.")
    if st.button("🎙️ Click to Answer"):
        st.info("Recording... (simulated)")
        st.info("Timeout reached. Showing ideal answer:")
        st.success("Ideal Answer: I'm a recent graduate with experience in Python and ML...")

    score = st.slider("AI Rating (out of 10)", 0, 10, 7)
    if score < 6:
        st.warning("You scored below 6. Please retake the mock interview.")

    st.markdown("---")
    st.subheader("Practice More Interviews")
    if st.button("Start Practice Interview"):
        st.success("Practice session started...")

    st.markdown("---")
    st.subheader("📚 Ask LAKS (Study Support Only)")
    user_input = st.text_input("Ask a question:")
    if user_input:
        if any(word in user_input.lower() for word in ["joke", "date", "abuse", "fight"]):
            st.error("LAKS only answers educational queries. Please be respectful.")
        else:
            st.success("AI Answer: Here's what I found on that topic...")

# --- Misuse Handling ---
if "abuse_count" not in st.session_state:
    st.session_state["abuse_count"] = 0
if st.session_state["abuse_count"] >= 3:
    st.error("You have been blocked for misuse. Please try again in 7 days.")
    st.stop()
