import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

def show_attendance_page():
    st.header("🕒 Teacher Clock-In / Clock-Out")

    try:
        response = requests.get(f"{API_URL}/users/teachers")
        if response.status_code == 200:
            teachers = response.json()
            teacher_options = {t['full_name']: t['id'] for t in teachers}
            
            # Default to logged-in user if possible
            current_user = st.session_state.get('full_name', list(teacher_options.keys())[0])
            if current_user in teacher_options:
                selected_name = st.selectbox("Select Your Name", list(teacher_options.keys()), index=list(teacher_options.keys()).index(current_user))
            else:
                selected_name = st.selectbox("Select Your Name", list(teacher_options.keys()))
                
            selected_id = teacher_options[selected_name]

            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🟢 Clock In", width="stretch"):
                    res = requests.post(f"{API_URL}/attendance/clock-in", json={"teacher_id": selected_id})
                    if res.status_code == 200:
                        st.success(f"Success: {res.json()['message']}")
                    else:
                        st.error(res.json()['detail'])

            with col2:
                if st.button("🔴 Clock Out", width="stretch"):
                    res = requests.post(f"{API_URL}/attendance/clock-out", json={"teacher_id": selected_id})
                    if res.status_code == 200:
                        st.warning(f"Success: {res.json()['message']}")
                    else:
                        st.error(res.json()['detail'])

            st.divider()
            st.subheader("📜 Your Attendance History")
            history_res = requests.get(f"{API_URL}/attendance/view/{selected_id}")
            if history_res.status_code == 200:
                logs = history_res.json()
                if logs:
                    df = pd.DataFrame(logs)
                    df = df[["clock_in_time", "clock_out_time"]]
                    st.dataframe(df, width="stretch")
                else:
                    st.info("No attendance records found.")
        else:
            st.error("Could not load teachers list.")
    except Exception as e:
        st.error(f"Connection Error: {e}")


    # ... (Copy the rest of the logic from app.py here) ...
    # Ensure you copy everything inside the original 'elif' block