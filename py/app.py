import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"  # Address of your FastAPI backend

st.set_page_config(page_title="EduSmart School System", layout="wide")
st.title("🏫 EduSmart School Management")

# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.selectbox(
    "Select Module",
    [
        "Home", 
        "Teacher Attendance (Clock In)", 
        "Student Grades", 
        "Schedule & Availability",   # <--- ADD THIS LINE HERE
        "Admin Panel"
    ]
)

# --- HOME PAGE ---
if menu == "Home":
    st.image("https://img.freepik.com/free-vector/school-building-with-students_107791-12249.jpg", width=600)
    st.write("### Welcome to the EduSmart System")
    st.info("Use the sidebar to navigate between modules.")

# --- MODULE C: TEACHER ATTENDANCE ---
elif menu == "Teacher Attendance (Clock In)":
    st.header("🕒 Teacher Clock-In / Clock-Out")

    # Step 1: Get list of teachers to populate the dropdown
    try:
        response = requests.get(f"{API_URL}/users/teachers")
        if response.status_code == 200:
            teachers = response.json()
            # Create a dictionary { "Mr. Bond": 1, "Ms. Smith": 2 }
            teacher_options = {t['full_name']: t['id'] for t in teachers}
            
            selected_name = st.selectbox("Select Your Name", list(teacher_options.keys()))
            selected_id = teacher_options[selected_name]

            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🟢 Clock In", use_container_width=True):
                    # Call the API
                    res = requests.post(f"{API_URL}/attendance/clock-in", json={"teacher_id": selected_id})
                    if res.status_code == 200:
                        st.success(f"Success: {res.json()['message']}")
                    else:
                        st.error(res.json()['detail'])

            with col2:
                if st.button("🔴 Clock Out", use_container_width=True):
                    res = requests.post(f"{API_URL}/attendance/clock-out", json={"teacher_id": selected_id})
                    if res.status_code == 200:
                        st.warning(f"Success: {res.json()['message']}")
                    else:
                        st.error(res.json()['detail'])

            # Show History
            st.divider()
            st.subheader("📜 Your Attendance History")
            history_res = requests.get(f"{API_URL}/attendance/view/{selected_id}")
            if history_res.status_code == 200:
                logs = history_res.json()
                if logs:
                    df = pd.DataFrame(logs)
                    # Clean up the table for display
                    df = df[["clock_in_time", "clock_out_time"]]
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No attendance records found.")
        else:
            st.error("Could not load teachers list.")
    except Exception as e:
        st.error(f"Connection Error: Is the backend running? {e}")

# --- MODULE E: STUDENT GRADES ---
elif menu == "Student Grades":
    st.header("📊 Student Performance Tracker")

    # 1. Add New Grade Form
    with st.expander("➕ Add New Grade"):
        # Fetch students
        try:
            stu_res = requests.get(f"{API_URL}/students/all")
            if stu_res.status_code == 200:
                students = stu_res.json()
                if students:
                    stu_options = {s['full_name']: s['id'] for s in students}
                    
                    with st.form("grade_form"):
                        s_name = st.selectbox("Student", list(stu_options.keys()))
                        subject = st.text_input("Subject (e.g. Math)")
                        score = st.number_input("Score (0-100)", 0, 100)
                        term = st.selectbox("Term", ["Mid-Term", "Finals"])
                        
                        submitted = st.form_submit_button("Submit Grade")
                        if submitted:
                            payload = {
                                "student_id": stu_options[s_name],
                                "subject": subject,
                                "score": score,
                                "term": term
                            }
                            res = requests.post(f"{API_URL}/grades/add", json=payload)
                            if res.status_code == 200:
                                st.success("Grade Added!")
                            else:
                                st.error("Failed to add grade.")
                else:
                    st.warning("No students found. Add students in Admin Panel.")
            else:
                st.error("Error fetching students.")
        except:
            st.error("Backend offline.")

    # 2. View Grades & Analytics
    st.divider()
    st.subheader("📈 Student Report Card")
    
    # Re-fetch students for the report view
    try:
        stu_res = requests.get(f"{API_URL}/students/all")
        if stu_res.status_code == 200:
            students = stu_res.json()
            stu_options = {s['full_name']: s['id'] for s in students}
            
            report_student_name = st.selectbox("Select Student to View", list(stu_options.keys()), key="report_select")
            report_student_id = stu_options[report_student_name]
            
            if st.button("Get Report"):
                report_res = requests.get(f"{API_URL}/grades/student/{report_student_id}")
                if report_res.status_code == 200:
                    grades_data = report_res.json()
                    df = pd.DataFrame(grades_data)
                    
                    # Display Data
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.dataframe(df[["subject", "score", "term"]])
                    
                    with col2:
                        # Identify Good vs Bad
                        avg_score = df["score"].mean()
                        st.metric("Average Score", f"{avg_score:.1f}")
                        
                        # Simple Bar Chart
                        st.bar_chart(df.set_index("subject")["score"])
                        
                        # Your specific requirement: Check "Bad Grades"
                        bad_grades = df[df["score"] < 40]
                        if not bad_grades.empty:
                            st.error(f"⚠️ Intervention Needed: Failing {len(bad_grades)} subjects.")
                        else:
                            st.success("✅ Student is performing well!")
                else:
                    st.warning("No grades found for this student.")
    except:
        pass

# --- ADMIN PANEL (Helper to add users/students quickly) ---
elif menu == "Admin Panel":
    st.header("🛠️ Admin Tools")
    
    tab1, tab2 = st.tabs(["Register Teacher", "Add Student"])
    
    with tab1:
        with st.form("reg_teacher"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            new_name = st.text_input("Full Name")
            if st.form_submit_button("Register"):
                payload = {"username": new_user, "password": new_pass, "full_name": new_name, "role": "teacher"}
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

# ... Add "Schedule & Availability" to your menu list first ...

# --- MODULE B: SCHEDULE & AVAILABILITY ---
elif menu == "Schedule & Availability":
    st.header("📅 Timetable & Availability")

    # Fetch teachers to select who we are acting as
    teachers_res = requests.get(f"{API_URL}/users/teachers")
    if teachers_res.status_code == 200:
        teachers = teachers_res.json()
        teacher_options = {t['full_name']: t['id'] for t in teachers}
        
        selected_teacher = st.selectbox("Select Teacher", list(teacher_options.keys()))
        teacher_id = teacher_options[selected_teacher]

        tab1, tab2 = st.tabs(["View Timetable", "Set Busy Time"])

        # TAB 1: VIEW VISUAL TIMETABLE
        with tab1:
            st.subheader(f"📅 Weekly Timetable: {selected_teacher}")
            
            if st.button("Refresh Schedule"):
                res = requests.get(f"{API_URL}/schedule/view/{teacher_id}")
                if res.status_code == 200:
                    data = res.json()
                    
                    if data:
                        # 1. Define Time Slots
                        time_slots = [
                            "08:00:00", "08:30:00", 
                            "09:00:00", "09:30:00", 
                            "10:00:00", "10:30:00", 
                            "11:00:00", "11:20:00", 
                            "12:00:00", "12:10:00", 
                            "13:00:00"
                        ]
                        
                        display_slots = [
                            "08:00 - 09:00", 
                            "09:00 - 10:00", 
                            "10:00 - 10:30 (LUNCH)", 
                            "10:30 - 11:20", 
                            "11:20 - 12:10", 
                            "12:10 - 01:00"
                        ]
                        
                        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                        schedule_df = pd.DataFrame("", index=display_slots, columns=days)
                        schedule_df.loc["10:00 - 10:30 (LUNCH)"] = "☕ LUNCH BREAK"

                        # 2. Fill the grid
                        for item in data:
                            day = item['day_of_week']
                            start = item['start_time']
                            subject = item['subject']
                            raw_room = item['room'] # e.g. "Rm 204" or "Class 1"
                            
                            # LOGIC: Change "Rm" to "Class" for display
                            # "Rm 204" becomes "Class 204"
                            # "Class 1" stays "Class 1"
                            display_room = raw_room.replace("Rm", "Class")
                            
                            cell_content = f"{subject}\n({display_room})"
                            
                            # Map API time to Display Slots
                            row_name = None
                            if start.startswith("08:00"): row_name = "08:00 - 09:00"
                            elif start.startswith("09:00"): row_name = "09:00 - 10:00"
                            elif start.startswith("10:30"): row_name = "10:30 - 11:20"
                            elif start.startswith("11:20"): row_name = "11:20 - 12:10"
                            elif start.startswith("12:10"): row_name = "12:10 - 01:00"
                            
                            if row_name:
                                schedule_df.at[row_name, day] = cell_content

                        # 3. Styling Function
                        def style_schedule(val):
                            base_style = 'color: black; text-align: center; vertical-align: middle; border: 1px solid white;'
                            
                            if val == "☕ LUNCH BREAK":
                                return base_style + 'background-color: #f0f0f0; font-weight: bold; color: #555;'
                            
                            elif val != "":
                                # LOGIC: Check if it's "New" (Class 1-10) or "Standard" (Class 100+)
                                # We check if the string contains "Class 1)", "Class 2)", etc.
                                is_new_class = False
                                for i in range(1, 11):
                                    if f"(Class {i})" in val:
                                        is_new_class = True
                                        break
                                
                                if is_new_class:
                                    # ORANGE for Manual Admin Entries
                                    return base_style + 'background-color: #ffcc80; font-weight: bold;'
                                else:
                                    # GREEN for Standard Seed Data
                                    return base_style + 'background-color: #d4edda; font-weight: bold;'
                            
                            else:
                                return 'color: #eee;' # Hide empty dashes

                        st.dataframe(
                            schedule_df.style.map(style_schedule), 
                            use_container_width=True,
                            height=350
                        )
                    else:
                        st.info("No classes found for this teacher.")
                else:
                    st.error("Error fetching schedule.")
                    
        # TAB 2: SET AVAILABILITY (The Option B Logic)
        with tab2:
            st.subheader("Mark Busy / Unavailable Slots")
            st.write("This helps the system avoid assigning you substitutes during these times.")
            
            with st.form("avail_form"):
                day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                start = st.time_input("Start Time")
                end = st.time_input("End Time")
                
                submitted = st.form_submit_button("Mark as BUSY")
                if submitted:
                    # Convert time to string for API (e.g. 14:00)
                    payload = {
                        "teacher_id": teacher_id,
                        "day_of_week": day,
                        "start_time": str(start),
                        "end_time": str(end),
                        "status": "BUSY"
                    }
                    res = requests.post(f"{API_URL}/availability/set", json=payload)
                    if res.status_code == 200:
                        st.success("Availability preferences saved!")
                    else:
                        st.error("Error saving availability.")

    # ADMIN SECTION TO ADD CLASSES (Put this in your Admin Panel or here for testing)
    # ADMIN SECTION TO ADD CLASSES
    st.divider()
    with st.expander("Admin: Assign Class to Schedule"):
        with st.form("add_class"):
            # 1. Define Options
            days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            
            # User Request: Existing Subjects
            subjects_list = ["Mathematics", "Science", "History", "English", "Physics"]
            
            # User Request: Class 1 - 10
            rooms_list = [f"Class {i}" for i in range(1, 11)] # Generates "Class 1" to "Class 10"
            # Add Labs just in case
            rooms_list.extend(["Lab 1", "Lab 2", "Computer Room"])

            # 2. Form Inputs
            day_a = st.selectbox("Day", days_list, key="d_a")
            
            # Time Inputs (Columns for better layout)
            c1, c2 = st.columns(2)
            with c1:
                start_a = st.selectbox("Start Time", [
                    "08:00", "09:00", "10:30", "11:20", "12:10"
                ])
            with c2:
                end_a = st.selectbox("End Time", [
                    "09:00", "10:00", "11:20", "12:10", "13:00"
                ])

            # The Dropdowns you asked for
            subj_a = st.selectbox("Subject", subjects_list)
            room_a = st.selectbox("Room", rooms_list)
            
            if st.form_submit_button("Assign Class"):
                payload = {
                    "teacher_id": teacher_id,
                    "day_of_week": day_a,
                    "start_time": start_a,
                    "end_time": end_a,
                    "subject": subj_a,
                    "room": room_a
                }
                res = requests.post(f"{API_URL}/schedule/add", json=payload)
                if res.status_code == 200:
                    st.success(f"Assigned {subj_a} to {room_a} on {day_a}!")
                else:
                    st.error("Failed to assign class.")