# seed_data.py
from sqlalchemy.orm import Session
# 👇 FIXED IMPORTS: 
from backend.database import engine, Base
from backend.models import User, Student, Schedule, Grade
from datetime import datetime, time
import random

# 1. CLEANUP & RESET
print("♻️  Resetting Database for High-Traffic Simulation...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

session = Session(bind=engine)

# --- A. CREATE TEACHERS ---
print("👨‍🏫 Hiring Teachers...")
teachers_data = [
    {"name": "Mr. John Smith",    "user": "math1", "subject": "Mathematics", "phone": "60123456780"},
    {"name": "Ms. Ada Lovelace",  "user": "math2", "subject": "Mathematics", "phone": "60123456781"},
    {"name": "Ms. Sarah Connor",  "user": "sci1",  "subject": "Science",     "phone": "60123456782"},
    {"name": "Dr. Emmett Brown",  "user": "sci2",  "subject": "Science",     "phone": "60123456783"},
    {"name": "Mrs. Ellen Ripley", "user": "eng1",  "subject": "English",     "phone": "60123456784"},
    {"name": "Mr. Shakespeare",   "user": "eng2",  "subject": "English",     "phone": "60123456785"},
    {"name": "Dr. Alan Grant",    "user": "hist1", "subject": "History",     "phone": "60123456786"},
    {"name": "Cikgu Siti",        "user": "bm1",   "subject": "Bahasa Melayu", "phone": "60123456787"},
    {"name": "Encik Razak",       "user": "bm2",   "subject": "Bahasa Melayu", "phone": "60123456788"},
    {"name": "Ms. Lara Croft",    "user": "geo1",  "subject": "Geography",   "phone": "60123456789"},
    {"name": "Mr. Bob Ross",      "user": "art1",  "subject": "Art",         "phone": "60123456790"},
    {"name": "Mr. Neo Anderson",  "user": "it1",   "subject": "Computer Science", "phone": "60123456791"},
    {"name": "Coach Carter",      "user": "pe1",   "subject": "P.E.",        "phone": "60123456792"},
]

all_teachers = []
db_teachers_by_subj = {} 

for t in teachers_data:
    new_t = User(username=t["user"], full_name=t["name"], password_hash="123", role="teacher", phone_number=t["phone"])
    session.add(new_t)
    all_teachers.append(new_t)
    # Commit partially to generate IDs so we can use them
    session.commit() 
    
    if t["subject"] not in db_teachers_by_subj: db_teachers_by_subj[t["subject"]] = []
    db_teachers_by_subj[t["subject"]].append(new_t)

# --- B. CREATE STUDENTS ---
print("🎓 Enrolling Students...")
class_names = ["5 Science A", "4 Arts B", "3 Junior C"]
first_names = ["Ali", "Chong", "Muthu", "Sarah", "David", "Amina", "Mei", "Raj", "Jessica", "Omar", "Jenny", "Kevin", "Siti", "Ah Meng", "Gopal", "Lisa", "Tom", "Nurul", "Ben", "Diana"]
last_names = ["Tan", "Lee", "Wong", "Singh", "Abdullah", "Razak", "Lim", "Krishnan", "Smith", "Fernandez"]

# Define subjects per class
class_subjects_map = {
    "5 Science A": ["Mathematics", "Science", "English", "Bahasa Melayu", "Computer Science"],
    "4 Arts B":    ["Art", "Bahasa Melayu", "Mathematics", "Geography", "English"],
    "3 Junior C":  ["P.E.", "History", "Science", "Art", "Mathematics"]
}

all_students = []

for class_name in class_names:
    for i in range(20): 
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        new_s = Student(full_name=f"{fname} {lname}", class_name=class_name)
        session.add(new_s)
        all_students.append(new_s)

session.commit()

# --- C. GENERATE SCHEDULE ---
print("📅 Generating Master Timetable...")
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
time_slots = [(time(8,0), time(9,0)), (time(9,0), time(10,0)), (time(10,30), time(11,20)), (time(11,20), time(12,10)), (time(12,10), time(13,0))]

for day in days:
    for slot_idx, (start_t, end_t) in enumerate(time_slots):
        busy_teachers = []
        for class_name, subjects in class_subjects_map.items():
            subj_idx = (slot_idx + days.index(day)) % len(subjects)
            subject = subjects[subj_idx]
            candidates = db_teachers_by_subj.get(subject, [])
            
            # Find a teacher not busy in this slot
            teacher = next((t for t in candidates if t.id not in busy_teachers), None)
            
            if teacher:
                room = f"Class {class_name[0]}" # e.g. "Class 5"
                session.add(Schedule(teacher_id=teacher.id, day_of_week=day, start_time=start_t, end_time=end_t, subject=subject, room=room))
                busy_teachers.append(teacher.id)
session.commit()

# --- D. GENERATE GRADES ---
print("📊 Grading Exams...")

for student in all_students:
    subjects = class_subjects_map[student.class_name]
    student_type = random.choices(["Smart", "Average", "Struggling"], weights=[0.2, 0.6, 0.2])[0]
    
    for subj in subjects:
        if student_type == "Smart":
            score = random.randint(75, 100)
        elif student_type == "Average":
            score = random.randint(40, 80)
        else:
            score = random.randint(15, 55)
            
        session.add(Grade(student_id=student.id, subject=subj, score=score, term="Mid-Term"))

session.commit()

# --- E. ADMIN ---
admin = User(username="admin", full_name="Principal Skinner", password_hash="admin123", role="admin", phone_number="60199999999")
session.add(admin)
session.commit()

print("✅ DONE! Database populated.")