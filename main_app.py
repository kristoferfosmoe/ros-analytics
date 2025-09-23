import streamlit as st
import json
import os

# Page config
st.set_page_config(page_title="GUIDON ROS2 Bag Analyzer", layout="wide")

# Load config
def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {"username": "guidon", "password": "uwb"}  # fallback

config = load_config()

# Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == config["username"] and password == config["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", ["Home", "Current Flight Analysis", "Historical Flight Data"])
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
    if page == "Home":
        st.title("GUIDON ROS2 Bag Analyzer")
        st.markdown("Welcome to the GUIDON ROS2 bag analysis platform")
        
        st.subheader("Available Features:")
        st.write("• **Current Flight Analysis** - Process and analyze new ROS2 bag files")
        st.write("• **Historical Flight Data** - View results from previous flight analyses")
        
    elif page == "Current Flight Analysis":
        exec(open("pages/current_flight.py").read())
    elif page == "Historical Flight Data":
        exec(open("pages/historical_flights.py").read())