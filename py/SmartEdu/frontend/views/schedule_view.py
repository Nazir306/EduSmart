import streamlit as st
import requests
import urllib.parse
import textwrap

API_URL = "http://127.0.0.1:8000"

def show_schedule_page():
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
    
    # ... (Copy the rest of the logic here) ...