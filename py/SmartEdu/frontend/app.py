import streamlit as st
# Import the new views
from views import auth_view, attendance_view, grades_view, schedule_view, admin_view

st.set_page_config(page_title="EduSmart School System", layout="wide")
st.title("🏫 EduSmart School Management")

# --- GLOBAL HELPER ---
def require_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("⛔ You must be logged in to access this module.")
        st.stop()

# --- SIDEBAR ---
menu = st.sidebar.selectbox(
    "Select Module",
    [
        "Home", 
        "Teacher Attendance", 
        "Student Grades", 
        "Schedule & Availability",
        "Admin Panel"
    ]
)

# --- NAVIGATION LOGIC ---
if menu == "Home":
    auth_view.show_login_page()

elif menu == "Teacher Attendance":
    require_login()
    attendance_view.show_attendance_page()

elif menu == "Student Grades":
    require_login()
    grades_view.show_grades_page()

elif menu == "Schedule & Availability":
    require_login()
    schedule_view.show_schedule_page()

elif menu == "Admin Panel":
    require_login()
    admin_view.show_admin_page()