import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time 
import urllib.parse
import textwrap

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"

# --- GATEKEEPER FUNCTIONS ---
def require_login():
    """Stops the script if the user is not logged in."""
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("⛔ You must be logged in to access this module.")
        st.info("Please select 'Home' from the sidebar to log in.")
        st.stop()

def require_admin():
    """Stops the script if the user is NOT an admin."""
    require_login()
    if 'role' not in st.session_state or st.session_state['role'] != 'admin':
        st.error("⛔ ACCESS DENIED: This page is for Administrators only.")
        st.stop()

# ----------------------------------------------

st.set_page_config(page_title="EduSmart School System", layout="wide")
st.title("🏫 EduSmart School Management")

# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.selectbox(
    "Select Module",
    [
        "Home", 
        "Teacher Attendance (Clock In)", 
        "Student Grades", 
        "Schedule & Availability",
        "Admin Panel"
    ]
)

# --- HOME PAGE (LOGIN SYSTEM) ---
if menu == "Home":
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

# --- MODULE C: TEACHER ATTENDANCE ---
elif menu == "Teacher Attendance (Clock In)":
    require_login() 
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

# --- MODULE E: STUDENT GRADES ---
elif menu == "Student Grades":
    require_login() 
    st.header("📊 Student Performance Tracker")

    # 1. CREATE TABS
    # We split the page into two sections:
    # - Tab 1: For managing single students (Add grade, view report card)
    # - Tab 2: For seeing the big picture (Who is failing?)
    tab1, tab2 = st.tabs(["📝 Individual Report", "📈 Class Analytics (Teacher View)"])

    # --- TAB 1: INDIVIDUAL (Your Old Code Moved Here) ---
    with tab1:
        # A. Add New Grade
        with st.expander("➕ Add New Grade"):
            try:
                stu_res = requests.get(f"{API_URL}/students/all")
                if stu_res.status_code == 200:
                    students = stu_res.json()
                    if students:
                        stu_options = {s['full_name']: s['id'] for s in students}
                        
                        with st.form("grade_form"):
                            s_name = st.selectbox("Student", list(stu_options.keys()))
                            # Added more subjects to match your new database
                            subject = st.selectbox("Subject", ["Mathematics", "Science", "English", "History", "Bahasa Melayu", "Art", "P.E.", "Geography", "Computer Science"])
                            score = st.number_input("Score (0-100)", 0, 100)
                            term = st.selectbox("Term", ["Mid-Term", "Finals"])
                            
                            if st.form_submit_button("Submit Grade"):
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
                        st.warning("No students found.")
                else:
                    st.error("Error fetching students.")
            except:
                st.error("Backend offline.")

        st.divider()

        # B. View Individual Report
        st.subheader("🔎 View Student Report")
        try:
            stu_res = requests.get(f"{API_URL}/students/all")
            if stu_res.status_code == 200:
                students = stu_res.json()
                stu_options = {s['full_name']: s['id'] for s in students}
                
                report_student_name = st.selectbox("Select Student to View", list(stu_options.keys()), key="report_select")
                
                if st.button("Get Report"):
                    report_res = requests.get(f"{API_URL}/grades/student/{stu_options[report_student_name]}")
                    if report_res.status_code == 200:
                        grades_data = report_res.json()
                        df = pd.DataFrame(grades_data)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.dataframe(df[["subject", "score", "term"]], width="stretch")
                        with col2:
                            avg_score = df["score"].mean()
                            st.metric("Average Score", f"{avg_score:.1f}")
                            st.bar_chart(df.set_index("subject")["score"])
                            
                            bad_grades = df[df["score"] < 40]
                            if not bad_grades.empty:
                                st.error(f"⚠️ Intervention Needed: Failing {len(bad_grades)} subjects.")
                            else:
                                st.success("✅ Student is performing well!")
                    else:
                        st.warning("No grades found for this student.")
        except:
            pass

    # --- TAB 2: CLASS ANALYTICS (The New Feature) ---
    with tab2:
        st.subheader("🏫 Class Performance Overview")
        st.info("Identify students who are struggling across the class.")
        
        # Select Class
        class_options = ["5 Science A", "4 Arts B", "3 Junior C"]
        selected_class = st.selectbox("Select Class to Analyze", class_options)
        
        if st.button("📊 Analyze Class"):
            try:
                # Call the NEW endpoint we added to main.py
                res = requests.get(f"{API_URL}/grades/analytics/{selected_class}")
                
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        df = pd.DataFrame(data)
                        
                        # 1. METRICS ROW
                        avg_class_score = df["average"].mean()
                        failing_students = df[df["failed_count"] > 0].shape[0]
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Class Average", f"{avg_class_score:.1f}")
                        m2.metric("Total Students", len(df))
                        m3.metric("Students Needing Help", failing_students, delta=-failing_students, delta_color="inverse")
                        
                        st.divider()
                        
                        # 2. "AT RISK" TABLE (Highlighted Red)
                        st.write("### 🚨 Intervention Needed (At-Risk Students)")
                        st.caption("Students failing 1 or more subjects (< 40 marks).")
                        
                        at_risk_df = df[df["failed_count"] > 0].copy()
                        
                        if not at_risk_df.empty:
                            # Simple styling: Show data
                            st.dataframe(
                                at_risk_df[["name", "average", "failed_subjects", "failed_count"]],
                                width="stretch"
                            )
                        else:
                            st.success("🎉 Amazing! No students are failing in this class.")

                        st.divider()

                        # 3. FULL RANKING
                        with st.expander("View Full Class Ranking"):
                            st.dataframe(
                                df[["name", "average", "failed_count"]], 
                                width="stretch"
                            )
                    else:
                        st.info("No grades found for this class yet.")
                else:
                    st.error("Error fetching analytics.")
            except Exception as e:
                st.error(f"Connection Error: {e}")

# --- MODULE B: SCHEDULE & AVAILABILITY ---
elif menu == "Schedule & Availability":
    require_login() 
    
    st.header("📅 Schedule & Substitution Center")

    teachers_res = requests.get(f"{API_URL}/users/teachers")
    if teachers_res.status_code == 200:
        teachers = teachers_res.json()
        teacher_options = {t['full_name']: t['id'] for t in teachers}
        
        current_user = st.session_state.get('full_name', list(teacher_options.keys())[0])
        idx = 0
        if current_user in teacher_options:
            idx = list(teacher_options.keys()).index(current_user)
            
        selected_teacher = st.selectbox("Viewing Schedule For:", list(teacher_options.keys()), index=idx)
        teacher_id = teacher_options[selected_teacher]

        # --- TABS CONFIGURATION ---
        tab1, tab2, tab3 = st.tabs(["📅 Master Timetable", "⛔ Set Busy/Unavailable", "🤖 AI Find Replacement"])

        # --- TAB 1: MASTER TIMETABLE VIEW (FIXED COLOR) ---
        with tab1:
            st.subheader("🏫 Master School Timetable")
            st.caption("View all classes across the entire school week.")

            if st.button("🔄 Refresh Master Schedule"):
                try:
                    res = requests.get(f"{API_URL}/schedule/master")
                    if res.status_code == 200:
                        data = res.json()
                        
                        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                        time_map = {
                            "08:00": "08:00 - 09:00",
                            "09:00": "09:00 - 10:00",
                            "10:00": "10:00 - 10:30 (BREAK)",
                            "10:30": "10:30 - 11:20",
                            "11:20": "11:20 - 12:10",
                            "12:10": "12:10 - 01:00"
                        }
                        
                        schedule_grid = {t: {d: [] for d in days} for t in time_map.values()}
                        
                        for item in data:
                            d = item['day']
                            s = item['start']
                            
                            slot_key = None
                            if s.startswith("08"): slot_key = time_map["08:00"]
                            elif s.startswith("09"): slot_key = time_map["09:00"]
                            elif s.startswith("10") and int(s[3:5]) >= 30: slot_key = time_map["10:30"]
                            elif s.startswith("11"): slot_key = time_map["11:20"]
                            elif s.startswith("12"): slot_key = time_map["12:10"]
                            
                            if slot_key and d in days:
                                schedule_grid[slot_key][d].append(item)

                        color_map = {
                            "Mathematics": "#e3f2fd", 
                            "Science":     "#e8f5e9", 
                            "English":     "#fff3e0", 
                            "History":     "#fff9c4", 
                            "Physics":     "#f3e5f5", 
                            "Default":     "#f5f5f5"
                        }

                        # 🔥 FIX: Added 'color: #000000;' to .badge to force black text
                        html_start = textwrap.dedent("""
                        <style>
                            table {width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px;}
                            th {background-color: #424242; color: white; padding: 10px; text-align: center;}
                            td {border: 1px solid #ddd; padding: 5px; vertical-align: top; height: 100px;}
                            .badge {
                                display: block; 
                                padding: 4px; 
                                margin-bottom: 4px; 
                                border-radius: 4px; 
                                border-left: 4px solid #555; 
                                box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
                                color: #000000 !important; /* <--- FORCES BLACK TEXT */
                            }
                            .teacher-name {font-weight: bold; font-size: 11px; color: #000000 !important;}
                            .room-name {font-size: 10px; color: #333333 !important;}
                        </style>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width:10%;">Time</th>
                                    <th style="width:18%;">Monday</th>
                                    <th style="width:18%;">Tuesday</th>
                                    <th style="width:18%;">Wednesday</th>
                                    <th style="width:18%;">Thursday</th>
                                    <th style="width:18%;">Friday</th>
                                </tr>
                            </thead>
                            <tbody>
                        """)
                        
                        html_body = ""
                        for time_slot, row_data in schedule_grid.items():
                            if "BREAK" in time_slot:
                                html_body += f"<tr style='background-color: #eee;'><td style='font-weight:bold; text-align:center; color:#000;'>{time_slot}</td><td colspan='5' style='text-align:center; color:#555; font-style:italic;'>☕ LUNCH BREAK</td></tr>"
                                continue

                            # Make the time column explicitly black too for visibility
                            html_body += f"<tr><td style='font-weight:bold; text-align:center; color: #e0e0e0;'>{time_slot}</td>"
                            
                            for day in days:
                                classes = row_data[day]
                                cell_content = ""
                                for c in classes:
                                    bg_color = color_map.get(c['subject'], color_map["Default"])
                                    card_html = f"""<div class="badge" style="background-color: {bg_color};">
<div class="teacher-name">👤 {c['teacher']}</div>
<div>📘 {c['subject']}</div>
<div class="room-name">📍 {c['room']}</div>
</div>"""
                                    cell_content += card_html
                                    
                                html_body += f"<td>{cell_content}</td>"
                            html_body += "</tr>"
                        
                        html_end = "</tbody></table>"
                        
                        full_html = html_start + html_body + html_end
                        st.markdown(full_html, unsafe_allow_html=True)

                    else:
                        st.error("Could not fetch Master Schedule.")
                except Exception as e:
                    st.error(f"Error: {e}")

        # --- TAB 2: SET AVAILABILITY ---
        with tab2:
            st.subheader("Mark Busy Slots")
            st.caption("Prevent the AI from recommending you during these times.")
            
            with st.form("avail_form"):
                day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                c1, c2 = st.columns(2)
                with c1: start = st.time_input("Start Time")
                with c2: end = st.time_input("End Time")
                
                if st.form_submit_button("💾 Mark as Busy"):
                    payload = {
                        "teacher_id": teacher_id,
                        "day_of_week": day,
                        "start_time": str(start),
                        "end_time": str(end),
                        "status": "BUSY"
                    }
                    res = requests.post(f"{API_URL}/availability/set", json=payload)
                    if res.status_code == 200:
                        st.success("Availability updated!")
                    else:
                        st.error("Failed to update.")

       # --- TAB 3: AI FIND REPLACEMENT ---
        with tab3:
            st.subheader("🤝 Find a Coverage Teacher")
            st.caption(f"Finding a substitute for: **{selected_teacher}**")

            with st.form("sub_search_form_tab"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    target_day = st.selectbox("Day Needed", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], key="sub_day")
                with c2:
                    target_time = st.selectbox("Start Time", ["08:00", "09:00", "10:30", "11:20", "12:10"], key="sub_time")
                with c3:
                    # Dropdown for subjects
                    subject_list = ["Mathematics", "Science", "History", "English", "Physics"]
                    target_subject = st.selectbox("Subject", subject_list, key="sub_subj")
                    
                target_end = "09:00" # Simplified
                
                search_submitted = st.form_submit_button("🔍 Find Available Colleagues")

            if search_submitted:
                st.divider()
                payload = {
                    "date": "2024-01-01",
                    "day_of_week": target_day,
                    "start_time": target_time,
                    "end_time": target_end,
                    "subject_needed": target_subject
                }

                try:
                    with st.spinner("🤖 AI is checking everyone's schedule..."):
                        res = requests.post(f"{API_URL}/ai/recommend-substitute", json=payload)
                    
                    if res.status_code == 200:
                        candidates = res.json()
                        if candidates:
                            st.success(f"✅ Found {len(candidates)} available teachers!")
                            
                            for t in candidates:
                                # LOGIC: High Score (>10) means they teach the same subject
                                is_top_match = t['score'] > 10
                                
                                # 1. Set the Label (No Numbers!)
                                if is_top_match:
                                    label_text = f"🌟 TOP MATCH: {t['name']}"
                                else:
                                    label_text = f"👤 {t['name']}"

                                with st.expander(label_text, expanded=is_top_match):
                                    # 2. Highlight "Perfect Matches" with a Yellow Box
                                    if is_top_match:
                                        st.warning(f"⭐ **Perfect Substitute:** {t['name']} also teaches **{target_subject}**!")
                                    else:
                                        st.caption(f"✅ Available: {t['reason']}")
                                    
                                    # 3. WhatsApp Logic
                                    msg_text = f"Hi {t['name']}, are you free to cover {target_subject} on {target_day} at {target_time}? The system shows you are free."
                                    phone = t.get('phone')
                                    
                                    if phone:
                                        encoded_msg = urllib.parse.quote(msg_text)
                                        whatsapp_url = f"https://wa.me/{phone}?text={encoded_msg}"
                                        st.link_button(label=f"💬 WhatsApp {t['name']}", url=whatsapp_url)
                                    else:
                                        st.warning("No phone number found.")
                                        st.code(msg_text, language="text")
                                        st.caption("👆 Copy this message manually")
                        else:
                            st.warning("⚠️ No teachers are free at this time.")
                    else:
                        st.error("AI Service Offline.")
                except Exception as e:
                    st.error(f"Error: {e}")

    else:
        st.error("Could not load teacher list.")

# --- ADMIN PANEL ---
elif menu == "Admin Panel":
    require_admin() 
    
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