import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

def show_admin_page():
    # Only check for admin here if you want double security
    if 'role' not in st.session_state or st.session_state['role'] != 'admin':
        st.error("⛔ ACCESS DENIED")
        return

    st.header("🛠️ Admin Tools") 
    st.write("Welcome, Admin. You have full control.")

    # Fetch teachers for Assign Schedule Tab
    teachers_res = requests.get(f"{API_URL}/users/teachers")
    teacher_options = {}
    if teachers_res.status_code == 200:
        teachers = teachers_res.json()
        teacher_options = {t['full_name']: t['id'] for t in teachers}
    
    # 3 Tabs: Register Teacher, Add Student, Assign Schedule
    tab1, tab2, tab3 = st.tabs(["Register Teacher", "Add Student", "Assign Class Schedule"])
    
    with tab1:
        with st.form("reg_teacher"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            new_name = st.text_input("Full Name")
            new_phone = st.text_input("Phone Number (Format: 60123456789)")
            
            if st.form_submit_button("Register"):
                payload = {"username": new_user, "password": new_pass, "full_name": new_name, "role": "teacher", "phone_number": new_phone}
                res = requests.post(f"{API_URL}/users/register", json=payload)
                if res.status_code == 200:
                    st.success("Teacher Created!")
                else:
                    st.error(res.text)

    with tab2:
        with st.form("add_student"):
            stu_name = st.text_input("Student Name")
            stu_class = st.text_input("Class Name")
            if st.form_submit_button("Add Student"):
                payload = {"full_name": stu_name, "class_name": stu_class}
                res = requests.post(f"{API_URL}/students/add", json=payload)
                if res.status_code == 200:
                    st.success("Student Added!")
                else:
                    st.error(res.text)

    # NEW: Tab 3 for Schedule Assignment
    with tab3:
        st.subheader("Assign Class to Teacher")
        with st.form("admin_schedule_form"):
            t_name = st.selectbox("Select Teacher", list(teacher_options.keys()))
            
            day_a = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            
            c1, c2 = st.columns(2)
            with c1:
                start_a = st.selectbox("Start Time", ["08:00", "09:00", "10:30", "11:20", "12:10"])
            with c2:
                end_a = st.selectbox("End Time", ["09:00", "10:00", "11:20", "12:10", "13:00"])

            subj_a = st.selectbox("Subject", ["Mathematics", "Science", "History", "English", "Physics"])
            
            rooms_list = [f"Class {i}" for i in range(1, 11)]
            rooms_list.extend(["Lab 1", "Lab 2", "Computer Room"])
            room_a = st.selectbox("Room", rooms_list)
            
            if st.form_submit_button("📅 Assign to Schedule"):
                t_id = teacher_options[t_name]
                payload = {
                    "teacher_id": t_id,
                    "day_of_week": day_a,
                    "start_time": start_a,
                    "end_time": end_a,
                    "subject": subj_a,
                    "room": room_a
                }
                
                try:
                    res = requests.post(f"{API_URL}/schedule/add", json=payload)
                    if res.status_code == 200:
                        st.success(f"✅ Assigned {subj_a} to {t_name} on {day_a}!")
                    else:
                        st.error("Failed to assign class.")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # ... (Copy the rest of the logic here) ...