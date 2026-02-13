from sqlalchemy.orm import Session
from models import engine, User, Student, Schedule, Grade, Base, TeacherAvailability
from datetime import datetime, time
import random

# 1. CLEANUP & RESET
print("♻️  Resetting Database for Realistic Scenario...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

session = Session(bind=engine)

# --- A. CREATE TEACHERS ---
# We map specific teachers to specific subjects
teachers_config = [
    {"name": "Mr. John Smith", "user": "mr_smith", "subject": "Mathematics"},
    {"name": "Ms. Sarah Connor", "user": "ms_connor", "subject": "Science"},
    {"name": "Dr. Alan Grant", "user": "dr_grant", "subject": "History"},
    {"name": "Mrs. Ellen Ripley", "user": "mrs_ripley", "subject": "English"},
    {"name": "Prof. Charles X", "user": "prof_x", "subject": "Physics"},
]

db_teachers = {} 

for t in teachers_config:
    new_t = User(
        full_name=t["name"], 
        username=t["user"], 
        password_hash="123", 
        role="teacher"
    )
    session.add(new_t)
    session.flush()
    db_teachers[t["subject"]] = new_t

session.commit()
print("✅ Teachers Created.")

# --- B. CREATE STUDENTS ---
students = ["Alice Wonderland", "Bob Builder", "Charlie Chaplin", "Harry Potter", "Tony Stark"]
for name in students:
    session.add(Student(full_name=name, class_name="5 Science A"))
session.commit()
print("✅ Students Created.")

# --- C. CREATE REALISTIC SCHEDULE ---
# Scenario: 5 Science A has the same schedule every day (Mon-Fri)
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# The Schedule Slots (Time, Subject, Room)
# Note: 10:00-10:30 is LUNCH, so we skip it.
daily_slots = [
    {"start": time(8, 0),  "end": time(9, 0),   "subject": "Mathematics", "room": "Rm 101"},
    {"start": time(9, 0),  "end": time(10, 0),  "subject": "Science",     "room": "Lab 1"},
    # 10:00 - 10:30 LUNCH BREAK
    {"start": time(10, 30), "end": time(11, 20), "subject": "History",     "room": "Rm 204"},
    {"start": time(11, 20), "end": time(12, 10), "subject": "English",     "room": "Rm 105"},
    {"start": time(12, 10), "end": time(13, 0),  "subject": "Physics",     "room": "Lab 2"},
]

print("📅 Building Full Class Schedule...")

for day in days:
    for slot in daily_slots:
        # Find the teacher responsible for this subject
        teacher = db_teachers[slot["subject"]]
        
        new_class = Schedule(
            teacher_id=teacher.id,
            day_of_week=day,
            start_time=slot["start"],
            end_time=slot["end"],
            subject=slot["subject"],
            room=slot["room"]
        )
        session.add(new_class)

session.commit()
print("✅ Realistic Timetable Created (8am - 1pm).")
print("   - Lunch Break gap left at 10:00am.")