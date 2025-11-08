import streamlit as st
import os
import requests
import jwt

# Import the dashboard modules
from admin_app import main as admin_dashboard
from parent_app import main as parent_dashboard
from child_app import main as child_dashboard

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

def login_user(username, password):
    response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        token = response.json()["access_token"]
        st.session_state.token = token
        st.session_state.username = username
        # Decode the token to get the user's role
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        st.session_state.role = decoded_token.get("role")
        return True
    return False

def main():
    st.set_page_config(layout="wide")

    if 'token' not in st.session_state:
        # Show login page
        st.title("Project Sanjaya")
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(username, password):
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        if st.session_state.role == "admin":
            admin_dashboard()
        elif st.session_state.role == "parent":
            parent_dashboard()
        elif st.session_state.role == "child":
            child_dashboard()
        else:
            st.error("Unknown user role.")

if __name__ == "__main__":
    main()
