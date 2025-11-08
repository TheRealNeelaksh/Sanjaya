import streamlit as st
import os
import requests
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="project_sanjaya/.env")
JWT_SECRET = os.getenv("JWT_SECRET")

# Import the dashboard modules
from admin_app import main as admin_dashboard
from parent_app import main as parent_dashboard
from child_app import main as child_dashboard

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

def login_user(username, password):
    try:
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password}, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        token = response.json()["access_token"]
        st.session_state.token = token
        st.session_state.username = username
        # Decode the token to get the user's role
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        st.session_state.role = decoded_token.get("role")
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Login failed: {e.response.json().get('detail', 'Unknown error')}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the backend: {e}")
        return False
    except jwt.PyJWTError as e:
        st.error(f"Failed to decode token: {e}")
        return False

def main():
    st.set_page_config(layout="wide")

    if 'token' not in st.session_state:
        # Show login page
        st.title("Project Sanjaya")
        st.subheader("Login")
        st.write(f"Connecting to API at: {API_URL}") # Debug line
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(username, password):
                st.rerun()
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
