import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import plotly.express as px
from requests.auth import HTTPBasicAuth
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'password' not in st.session_state:
    st.session_state.password = ""

def make_authenticated_request(method, endpoint, data=None, params=None):
    url = f"{API_BASE_URL}{endpoint}"
    auth = HTTPBasicAuth(st.session_state.username, st.session_state.password)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, auth=auth, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, auth=auth, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, auth=auth, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, auth=auth)
        
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please ensure the FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"❌ Request error: {str(e)}")
        return None

def register_user(username, password, email):
    try:
        response = requests.post(f"{API_BASE_URL}/register", json={
            "username": username,
            "password": password,
            "email": email
        })
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please ensure the FastAPI server is running.")
        return None
    
def send_report(username, password, email):
    try:
        response = requests.post(f"{API_BASE_URL}/register", json={
            "username": username,
            "password": password,
            "email": email
        })
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please ensure the FastAPI server is running.")
        return None

def login_page():
    st.title("🔍 Uptime Monitor")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if username and password:
                # Test authentication by making a request to /me
                auth = HTTPBasicAuth(username, password)
                try:
                    response = requests.get(f"{API_BASE_URL}/me", auth=auth)
                    if response.status_code == 200:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.password = password
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API server. Please ensure the FastAPI server is running.")
            else:
                st.error("Please enter both username and password")
    
    with tab2:
        st.subheader("Register New Account")
        email = st.text_input("Email", key="reg_email")
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", type="primary"):
            if not all([new_username, new_password, confirm_password]):
                st.error("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("Passwords don't match")
            else:
                response = register_user(new_username, new_password, email)
                if response and response.status_code == 200:
                    st.success("✅ Registration successful! Please login with your new account.")
                elif response:
                    error_msg = response.json().get("detail", "Registration failed")
                    st.error(f"❌ {error_msg}")

def dashboard_page():
    st.title("🔍 Uptime Monitor Dashboard")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Welcome, **{st.session_state.username}**!")
        send_report_btn = st.button("Send Report", type="primary")
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.password = ""
            st.rerun()
    
    st.subheader("📝 Add New URL to Monitor")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_url = st.text_input("Enter URL to monitor:", placeholder="https://example.com")
    with col2:
        category = st.text_input("Category (optional):", placeholder="e.g., Production")
    with col3:
        st.write("")  # Spacing
        add_button = st.button("➕ Add URL", type="primary")
    
    if add_button and new_url:
        if not new_url.startswith(("http://", "https://")):
            new_url = "https://" + new_url
        
        data = {"url": new_url}
        if category:
            data["category"] = category
            
        response = make_authenticated_request("POST", "/track", data=data)
        if response and response.status_code == 200:
            st.success(f"✅ Successfully added {new_url} to monitoring!")
            time.sleep(1)
            st.rerun()
        elif response:
            error_msg = response.json().get("detail", "Failed to add URL")
            st.error(f"❌ {error_msg}")
            
    if send_report_btn:
        response = make_authenticated_request("POST", "/send-report", data=None)
        if response and response.status_code == 200:
            st.success(f"✅ Successfully sent report!")
            time.sleep(1)
            st.rerun()
        elif response:
            error_msg = response.json().get("detail", "Failed to add URL")
            st.error(f"❌ {error_msg}")
    
    st.divider()
    
    response = make_authenticated_request("GET", "/my-urls")
    if not response or response.status_code != 200:
        st.error("Failed to load your URLs")
        return
    
    data = response.json()
    urls = data.get("urls", [])
    
    if not urls:
        st.info("📋 No URLs being monitored yet. Add one above to get started!")
        return
    
    st.subheader(f"📊 Your Monitored URLs ({len(urls)} total)")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Check All URLs Now"):
            response = make_authenticated_request("POST", "/check-all")
            if response and response.status_code == 200:
                st.success("✅ All URLs checked successfully!")
                time.sleep(1)
                st.rerun()
    
    for i, url_data in enumerate(urls):
        url = url_data["url"]
        category = url_data.get("category", "")
        
        with st.container():
            status_response = make_authenticated_request("GET", f"/status/{url}")
            
            if status_response and status_response.status_code == 200:
                status = status_response.json()
                uptime = status["uptime_percentage"]
                last_checked = status.get("last_checked", "Never")
                
                if uptime >= 99:
                    status_color = "🟢"
                    uptime_color = "green"
                elif uptime >= 95:
                    status_color = "🟡"
                    uptime_color = "orange"
                else:
                    status_color = "🔴"
                    uptime_color = "red"
                
                col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1, 1])
                
                with col1:
                    st.write(f"**{url}**")
                    if category:
                        st.caption(f"📁 {category}")
                
                with col2:
                    st.metric("Uptime", f"{uptime}%", delta=None)
                    st.markdown(f"<span style='color: {uptime_color}'>{status_color}</span>", unsafe_allow_html=True)
                
                with col3:
                    if last_checked != "Never":
                        try:
                            last_check_dt = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
                            st.write("**Last Check:**")
                            st.caption(last_check_dt.strftime("%m/%d %H:%M"))
                        except:
                            st.caption("Recently")
                    else:
                        st.caption("Never checked")
                
                with col4:
                    if st.button(f"🔍 Details", key=f"details_{i}"):
                        st.session_state[f"show_details_{i}"] = not st.session_state.get(f"show_details_{i}", False)
                
                with col5:
                    if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                        st.session_state[f"confirm_remove_{i}"] = True
                
                if st.session_state.get(f"confirm_remove_{i}", False):
                    st.warning(f"Are you sure you want to remove {url}?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, Remove", key=f"confirm_yes_{i}"):
                            response = make_authenticated_request("DELETE", f"/urls/{url}")
                            if response and response.status_code == 200:
                                st.success("✅ URL removed successfully!")
                                del st.session_state[f"confirm_remove_{i}"]
                                time.sleep(1)
                                st.rerun()
                    with col_no:
                        if st.button("No, Cancel", key=f"confirm_no_{i}"):
                            del st.session_state[f"confirm_remove_{i}"]
                            st.rerun()
                
                if st.session_state.get(f"show_details_{i}", False):
                    with st.expander(f"📈 Details for {url}", expanded=True):
                        logs_response = make_authenticated_request("GET", f"/logs/{url}", params={"limit": 50})
                        
                        if logs_response and logs_response.status_code == 200:
                            logs = logs_response.json()
                            
                            if logs:
                                df = pd.DataFrame(logs)
                                df['timestamp'] = pd.to_datetime(df['timestamp'])
                                df = df.sort_values('timestamp', ascending=False)
                                
                                col_stats1, col_stats2, col_stats3 = st.columns(3)
                                with col_stats1:
                                    avg_response = df['response_time_ms'].mean()
                                    st.metric("Avg Response Time", f"{avg_response:.0f}ms")
                                with col_stats2:
                                    success_rate = (df['status'] == 'success').mean() * 100
                                    st.metric("Success Rate", f"{success_rate:.1f}%")
                                with col_stats3:
                                    total_checks = len(df)
                                    st.metric("Total Checks", total_checks)
                                
                                if len(df) > 1:
                                    st.subheader("📊 Response Time Over Time")
                                    fig = px.line(df.tail(20), x='timestamp', y='response_time_ms',
                                                title="Response Time (Last 20 checks)",
                                                labels={'response_time_ms': 'Response Time (ms)', 'timestamp': 'Time'})
                                    fig.update_layout(height=300)
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                st.subheader("📝 Recent Check Logs")
                                display_df = df.head(10).copy()
                                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                
                                def style_status(val):
                                    color = 'green' if val == 'success' else 'red'
                                    return f'color: {color}'
                                
                                styled_df = display_df.style.applymap(style_status, subset=['status'])
                                st.dataframe(styled_df, use_container_width=True)
                                
                                if st.button(f"🔄 Check {url} Now", key=f"check_now_{i}"):
                                    response = make_authenticated_request("POST", f"/check/{url}")
                                    if response and response.status_code == 200:
                                        st.success("✅ URL checked successfully!")
                                        time.sleep(1)
                                        st.rerun()
                            else:
                                st.info("No check logs available yet.")
                        else:
                            st.error("Failed to load logs for this URL.")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{url}**")
                    if category:
                        st.caption(f"📁 {category}")
                with col2:
                    st.write("❌ Status unavailable")
            
            st.divider()

def main():
    """Main application"""
    st.set_page_config(
        page_title="Uptime Monitor",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
    <style>
    .stAlert > div {
        padding: 0.5rem 1rem;
    }
    .metric-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()