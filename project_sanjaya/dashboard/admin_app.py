import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")

def login_user(username, password):
    response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.session_state.username = username
        return True
    return False

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def manage_users():
    st.subheader("User Management")
    # TODO: Implement user creation, deletion, etc.
    st.write("Coming soon...")

def link_parent_child():
    st.subheader("Link Parent to Child")
    # TODO: Implement logic to link parent and child accounts
    st.write("Coming soon...")

def manage_trips():
    st.subheader("Trip Management")
    # TODO: Implement trip pausing, ending, etc.
    st.write("Coming soon...")

def view_api_usage():
    st.subheader("API Usage")
    # TODO: Implement API call to get usage data
    st.write("Coming soon...")

def main():
    st.title("Admin Dashboard")

    if 'token' not in st.session_state:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            # A simple check for admin role, in a real app this would be handled by the backend
            if login_user(username, password) and st.session_state.username == 'admin':
                st.rerun()
            else:
                st.error("Invalid admin credentials.")
    else:
        st.subheader(f"Welcome, {st.session_state.username}!")

        manage_users()
        link_parent_child()
        manage_trips()
        view_api_usage()

if __name__ == "__main__":
    main()
