import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

def show_grades_page():
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
