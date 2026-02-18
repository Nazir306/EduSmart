import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

def show_login_page():
    st.image("https://img.freepik.com/free-vector/school-building-with-students_107791-12249.jpg", width=400)
    st.write("### Welcome to EduSmart")

    # If already logged in, show Logout button
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        st.success(f"✅ You are logged in as {st.session_state['full_name']} ({st.session_state['role']})")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
    
    # If NOT logged in, show Login Form
    else:
        st.subheader("🔐 Please Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                payload = {"username": username, "password": password}
                res = requests.post(f"{API_URL}/users/login", json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = data['role']
                    st.session_state['user_id'] = data['user_id']
                    st.session_state['full_name'] = data['full_name']
                    st.success("Login Successful!")
                    st.rerun() 
                else:
                    st.error("Invalid Username or Password")
            except Exception as e:
                st.error(f"Could not connect to server: {e}")