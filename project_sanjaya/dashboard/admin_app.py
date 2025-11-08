import streamlit as st
import requests
import os

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def manage_users():
    st.subheader("User Management")
    with st.expander("Create a new user"):
        with st.form("create_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["parent", "child"])
            submitted = st.form_submit_button("Create User")

            if submitted:
                response = requests.post(
                    f"{API_URL}/register",
                    headers=get_headers(),
                    json={"username": username, "password": password, "role": role}
                )
                if response.status_code == 200:
                    st.success(f"User '{username}' created successfully.")
                else:
                    st.error(f"Error creating user: {response.json()['detail']}")

def get_users(role):
    response = requests.get(f"{API_URL}/users?role={role}", headers=get_headers())
    if response.status_code == 200:
        return [user['username'] for user in response.json()]
    return []

def link_parent_child():
    st.subheader("Link Parent to Child")

    parents = get_users('parent')
    children = get_users('child')

    if not parents or not children:
        st.warning("No parents or children available to link.")
        return

    parent_username = st.selectbox("Select Parent", parents)
    child_username = st.selectbox("Select Child", children)

    if st.button("Link Parent to Child"):
        response = requests.post(
            f"{API_URL}/link-parent-child",
            headers=get_headers(),
            json={"parent_username": parent_username, "child_username": child_username}
        )
        if response.status_code == 200:
            st.success("Parent and child linked successfully.")
        else:
            st.error(f"Error linking parent and child: {response.json()['detail']}")

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
    st.subheader(f"Welcome, {st.session_state.username}!")

    manage_users()
    link_parent_child()
    manage_trips()
    view_api_usage()
