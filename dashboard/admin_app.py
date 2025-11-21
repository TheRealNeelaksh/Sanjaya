"""
Admin Dashboard for Project Sanjaya v2.1
Streamlit interface for admins to:
- Manage users
- Manage trips
- View API usage
- Control NGROK
"""
import streamlit as st
import requests
import json
import os


# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")


# Helper functions
def make_request(endpoint, method="GET", data=None, auth_token=None):
    """Make API request with error handling"""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return response
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def login(username, password):
    """Login and store token"""
    response = make_request("/login", "POST", {"username": username, "password": password})
    
    if response and response.status_code == 200:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.user = data["user"]
        return True
    else:
        return False


# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


# Main app
def main():
    st.set_page_config(
        page_title="Sanjaya - Admin Dashboard",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ Admin Dashboard - Project Sanjaya")
    
    # Authentication
    if not st.session_state.token:
        show_auth_page()
    else:
        show_dashboard()


def show_auth_page():
    """Show login page"""
    st.subheader("Admin Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if login(username, password):
            if st.session_state.user["role"] == "admin":
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("This dashboard is for admins only")
                st.session_state.token = None
                st.session_state.user = None
        else:
            st.error("Invalid credentials")


def show_dashboard():
    """Show main dashboard"""
    user = st.session_state.user
    token = st.session_state.token
    
    # Header
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.write(f"**Logged in as:** {user['username']} (Admin)")
    
    with col2:
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "🚗 Trips", "📊 API Usage", "🌐 NGROK"])
    
    with tab1:
        show_users_tab(token)
    
    with tab2:
        show_trips_tab(token)
    
    with tab3:
        show_api_usage_tab()
    
    with tab4:
        show_ngrok_tab()


def show_users_tab(token):
    """User management tab"""
    st.subheader("User Management")
    
    # Fetch all users
    response = make_request("/admin/users", auth_token=token)
    
    if response and response.status_code == 200:
        users = response.json()["users"]
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        
        child_count = sum(1 for u in users if u['role'] == 'child')
        parent_count = sum(1 for u in users if u['role'] == 'parent')
        admin_count = sum(1 for u in users if u['role'] == 'admin')
        
        with col1:
            st.metric("Total Users", len(users))
        with col2:
            st.metric("Children", child_count)
        with col3:
            st.metric("Parents", parent_count)
        
        st.divider()
        
        # Users table
        st.write("**All Users:**")
        
        for user in users:
            with st.expander(f"{user['username']} ({user['role']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {user['id']}")
                    st.write(f"**Role:** {user['role']}")
                
                with col2:
                    st.write(f"**Created:** {user['created_at'][:10]}")
    
    else:
        st.error("Failed to load users")
    
    st.divider()
    
    # Create new user
    st.subheader("Create New User")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_username = st.text_input("Username", key="new_user")
    with col2:
        new_password = st.text_input("Password", type="password", key="new_pass")
    with col3:
        new_role = st.selectbox("Role", ["child", "parent", "admin"])
    
    if st.button("Create User"):
        if not new_username or not new_password:
            st.error("Username and password required")
        else:
            response = make_request("/register", "POST", {
                "username": new_username,
                "password": new_password,
                "role": new_role
            })
            
            if response and response.status_code == 201:
                st.success(f"User '{new_username}' created successfully")
                st.rerun()
            else:
                st.error("Failed to create user")


def show_trips_tab(token):
    """Trip management tab"""
    st.subheader("Trip Management")
    
    # Fetch all trips
    response = make_request("/admin/trips", auth_token=token)
    
    if response and response.status_code == 200:
        trips = response.json()["trips"]
        
        # Statistics
        active_trips = [t for t in trips if t['status'] == 'active']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Trips", len(trips))
        with col2:
            st.metric("Active Trips", len(active_trips))
        
        st.divider()
        
        # Show active trips first
        if active_trips:
            st.write("**🟢 Active Trips:**")
            for trip in active_trips:
                with st.expander(f"{trip['username']} - {trip['mode']} (ID: {trip['id']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {trip['username']}")
                        st.write(f"**Mode:** {trip['mode']}")
                    
                    with col2:
                        st.write(f"**Status:** {trip['status']}")
                        st.write(f"**Started:** {trip['start_time'][:19]}")
        
        st.divider()
        
        # All trips
        st.write("**All Trips:**")
        
        for trip in trips[:20]:  # Show last 20
            status_icon = "🟢" if trip['status'] == 'active' else "⚫"
            st.write(f"{status_icon} {trip['username']} - {trip['mode']} - {trip['start_time'][:10]}")
    
    else:
        st.error("Failed to load trips")


def show_api_usage_tab():
    """API usage statistics tab"""
    st.subheader("AviationStack API Usage")
    
    # Load usage data
    usage_file = "logs/api_usage.json"
    
    if os.path.exists(usage_file):
        with open(usage_file, 'r') as f:
            data = json.load(f)
        
        total_calls = data.get("total_calls", 0)
        calls = data.get("calls", [])
        
        # Calculate monthly calls
        from datetime import datetime
        now = datetime.utcnow()
        monthly_calls = sum(
            1 for call in calls 
            if datetime.fromisoformat(call['timestamp']).month == now.month
        )
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total API Calls", total_calls)
        with col2:
            st.metric("This Month", monthly_calls)
        with col3:
            remaining = 100 - monthly_calls
            st.metric("Remaining", remaining, delta=f"{remaining}% of limit")
        
        # Warning if approaching limit
        if monthly_calls >= 90:
            st.error("⚠️ API limit almost reached! Only 10 calls remaining this month.")
        elif monthly_calls >= 70:
            st.warning("⚠️ API usage at 70%. Monitor usage carefully.")
        
        st.divider()
        
        # Recent calls
        st.write("**Recent API Calls:**")
        
        for call in reversed(calls[-10:]):  # Show last 10
            status_icon = "✅" if call['status'] == 'success' else "❌"
            st.write(f"{status_icon} {call['timestamp'][:19]} - {call['endpoint']} - {call.get('flight_number', 'N/A')}")
    
    else:
        st.info("No API usage data yet")


def show_ngrok_tab():
    """NGROK management tab"""
    st.subheader("NGROK Tunnel Management")
    
    st.info("NGROK tunnel must be started manually using the helper script")
    
    st.code("python scripts/ngrok_helper.py", language="bash")
    
    st.divider()
    
    st.write("**Current Configuration:**")
    st.write("- Free tier: 1 tunnel")
    st.write("- Port: 8000 (FastAPI)")
    st.write("- Tracking links: `/track/<username>-<session_hash>`")
    
    st.divider()
    
    st.write("**Testing Connection:**")
    
    ngrok_url = st.text_input("Enter NGROK URL", placeholder="https://xxxx.ngrok.io")
    
    if st.button("Test Connection"):
        if ngrok_url:
            try:
                response = requests.get(f"{ngrok_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Connection successful!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Connection failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")
        else:
            st.error("Please enter NGROK URL")


if __name__ == "__main__":
    main()