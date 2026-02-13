from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

# Import your database structure
import models
from models import SessionLocal, engine, TeacherAttendance, User, Student, Grade, Schedule, TeacherAvailability

# Create the database tables automatically when the app starts
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- UTILITY: Get Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DATA SCHEMAS (Pydantic Models) ---

class ClockInRequest(BaseModel):
    teacher_id: int

class ClockOutRequest(BaseModel):
    teacher_id: int

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "teacher"  # Default to "teacher", but can be "admin"
    phone_number: str

class StudentCreate(BaseModel):
    full_name: str
    class_name: str

class GradeCreate(BaseModel):
    student_id: int
    subject: str
    score: float
    term: str = "Finals"

class SubstitutionRequest(BaseModel):
    date: str          # "YYYY-MM-DD"
    day_of_week: str   # "Monday"
    start_time: str    # "09:00"
    end_time: str      # "10:00"
    subject_needed: str # "Mathematics"

# --- SCHEMAS FOR MODULE B (SCHEDULING) ---
class ScheduleCreate(BaseModel):
    teacher_id: int
    day_of_week: str  # e.g., "Monday"
    start_time: str   # e.g., "09:00"
    end_time: str     # e.g., "10:00"
    subject: str
    room: str

class AvailabilityCreate(BaseModel):
    teacher_id: int
    day_of_week: str
    start_time: str
    end_time: str
    status: str       # "BUSY" or "PREFERRED"

class LoginRequest(BaseModel):
    username: str
    password: str

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the School Management API"}

# ==========================================
# MODULE: USER MANAGEMENT (Register & View)
# ==========================================

@app.post("/users/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new teacher or admin account.
    """
    # 1. Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 2. Create new User object
    new_user = User(
        username=user.username,
        password_hash=user.password,  # In real app, hash this!
        full_name=user.full_name,
        role=user.role,
        phone_number=user.phone_number
    )

    # 3. Save to Database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"status": "success", "message": f"User {user.username} created successfully!", "user_id": new_user.id}

@app.get("/users/teachers")
def get_all_teachers(db: Session = Depends(get_db)):
    """
    Get a list of all users who have the role 'teacher'.
    """
    teachers = db.query(User).filter(User.role == "teacher").all()
    
    # Return a clean list (excluding passwords)
    return [
        {
            "id": t.id, 
            "full_name": t.full_name, 
            "username": t.username,
            "role": t.role
        } 
        for t in teachers
    ]

# ==========================================
# MODULE C: TEACHER ATTENDANCE
# ==========================================

@app.post("/attendance/clock-in")
def clock_in(request: ClockInRequest, db: Session = Depends(get_db)):
    """
    Teacher clicks 'Clock In'. 
    """
    # 1. Check if teacher exists
    teacher = db.query(User).filter(User.id == request.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # 2. Create the log
    new_log = TeacherAttendance(
        teacher_id=request.teacher_id,
        clock_in_time=datetime.now()
    )
    
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {"status": "success", "message": f"Teacher {request.teacher_id} clocked in!", "log_id": new_log.id}

@app.post("/attendance/clock-out")
def clock_out(request: ClockOutRequest, db: Session = Depends(get_db)):
    """
    Teacher clicks 'Clock Out'.
    """
    # Find the most recent attendance log for this teacher that has NO clock_out_time
    log = db.query(TeacherAttendance).filter(
        TeacherAttendance.teacher_id == request.teacher_id,
        TeacherAttendance.clock_out_time == None
    ).order_by(TeacherAttendance.clock_in_time.desc()).first()

    if not log:
        raise HTTPException(status_code=400, detail="You haven't clocked in yet!")

    # Update the log
    log.clock_out_time = datetime.now()
    db.commit()
    
    return {"status": "success", "message": f"Teacher {request.teacher_id} clocked out."}

@app.get("/attendance/view/{teacher_id}")
def view_attendance(teacher_id: int, db: Session = Depends(get_db)):
    """
    View history for a specific teacher.
    """
    logs = db.query(TeacherAttendance).filter(TeacherAttendance.teacher_id == teacher_id).all()
    return logs

# ==========================================
# MODULE E: STUDENTS & GRADES
# ==========================================

@app.post("/students/add")
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    """
    Add a new student to the database.
    """
    new_student = Student(
        full_name=student.full_name,
        class_name=student.class_name
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"status": "success", "student_id": new_student.id}

@app.get("/students/all")
def get_all_students(db: Session = Depends(get_db)):
    """
    View all students.
    """
    return db.query(Student).all()

@app.post("/grades/add")
def add_grade(grade: GradeCreate, db: Session = Depends(get_db)):
    """
    Add a grade for a student.
    """
    # Check if student exists first
    student = db.query(Student).filter(Student.id == grade.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    new_grade = Grade(
        student_id=grade.student_id,
        subject=grade.subject,
        score=grade.score,
        term=grade.term
    )
    db.add(new_grade)
    db.commit()
    return {"status": "success", "message": "Grade added"}

@app.get("/grades/student/{student_id}")
def get_student_report(student_id: int, db: Session = Depends(get_db)):
    """
    Get all grades for a specific student.
    """
    grades = db.query(Grade).filter(Grade.student_id == student_id).all()
    if not grades:
        raise HTTPException(status_code=404, detail="No grades found for this student")
    return grades

# ==========================================
# MODULE B: SCHEDULING & AVAILABILITY
# ==========================================

@app.post("/schedule/add")
def add_class_slot(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """
    Admin assigns a class to a teacher.
    """
    # Convert string time "09:00" to Python Time object
    s_time = datetime.strptime(schedule.start_time, "%H:%M").time()
    e_time = datetime.strptime(schedule.end_time, "%H:%M").time()

    new_slot = models.Schedule(
        teacher_id=schedule.teacher_id,
        day_of_week=schedule.day_of_week,
        start_time=s_time,
        end_time=e_time,
        subject=schedule.subject,
        room=schedule.room
    )
    db.add(new_slot)
    db.commit()
    return {"status": "success", "message": "Class scheduled successfully"}

@app.get("/schedule/view/{teacher_id}")
def view_schedule(teacher_id: int, db: Session = Depends(get_db)):
    """
    View the timetable for a specific teacher.
    """
    classes = db.query(models.Schedule).filter(models.Schedule.teacher_id == teacher_id).all()
    return classes

@app.post("/availability/set")
def set_availability(avail: AvailabilityCreate, db: Session = Depends(get_db)):
    """
    Teacher marks a slot as BUSY.
    """
    s_time = datetime.strptime(avail.start_time, "%H:%M").time()
    e_time = datetime.strptime(avail.end_time, "%H:%M").time()

    # (Optional Logic: Check if they already have a class then? For now, we keep it simple)
    
    new_avail = models.TeacherAvailability(
        teacher_id=avail.teacher_id,
        day_of_week=avail.day_of_week,
        start_time=s_time,
        end_time=e_time,
        status=avail.status
    )
    db.add(new_avail)
    db.commit()
    return {"status": "success", "message": "Availability updated"}

@app.get("/schedule/master")
def get_master_schedule(db: Session = Depends(get_db)):
    """
    Fetch ALL scheduled classes for the Master Timetable.
    Includes Teacher Name.
    """
    # Join Schedule with User to get teacher names
    results = db.query(
        models.Schedule.day_of_week,
        models.Schedule.start_time,
        models.Schedule.end_time,
        models.Schedule.subject,
        models.Schedule.room,
        User.full_name
    ).join(User, models.Schedule.teacher_id == User.id).all()

    # Format data for JSON
    master_list = []
    for day, start, end, subj, room, teacher in results:
        master_list.append({
            "day": day,
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "subject": subj,
            "room": room,
            "teacher": teacher
        })
    
    return master_list

@app.post("/users/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Checks if username and password match.
    """
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # NOTE: In a real app, we compare Hashes. Here we compare plain text for now.
    if user.password_hash != request.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    return {
        "status": "success", 
        "user_id": user.id, 
        "role": user.role,
        "full_name": user.full_name
    }

@app.post("/ai/recommend-substitute")
def recommend_substitute(req: SubstitutionRequest, db: Session = Depends(get_db)):
    """
    AI Logic to find the best substitute teacher.
    """
    # Convert string times to Python time objects
    try:
        req_start = datetime.strptime(req.start_time, "%H:%M").time()
        # Handle cases where end_time might be calculated differently
        req_end = datetime.strptime(req.end_time, "%H:%M").time()
    except ValueError:
        # Fallback if time format is wrong
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    # 1. Get all teachers
    all_teachers = db.query(User).filter(User.role == "teacher").all()
    candidates = []

    for teacher in all_teachers:
        is_available = True
        reason = "Available"
        score = 0

        # CHECK 1: CONFLICTS IN SCHEDULE (Is he already teaching?)
        conflict_class = db.query(models.Schedule).filter(
            models.Schedule.teacher_id == teacher.id,
            models.Schedule.day_of_week == req.day_of_week,
            models.Schedule.start_time == req_start
        ).first()

        if conflict_class:
            is_available = False
            reason = f"Busy: Teaching {conflict_class.subject}"

        # CHECK 2: BUSY STATUS (Did he mark himself as busy?)
        if is_available:
            busy_slot = db.query(models.TeacherAvailability).filter(
                models.TeacherAvailability.teacher_id == teacher.id,
                models.TeacherAvailability.day_of_week == req.day_of_week,
                models.TeacherAvailability.start_time == req_start,
                models.TeacherAvailability.status == "BUSY"
            ).first()
            
            if busy_slot:
                is_available = False
                reason = "Marked as Busy/Unavailable"

        # CHECK 3: SCORING (AI Logic)
        if is_available:
            score += 10 # Base score for being free
            
            # Bonus: Teaches the same subject?
            has_taught_subject = db.query(models.Schedule).filter(
                models.Schedule.teacher_id == teacher.id,
                models.Schedule.subject == req.subject_needed
            ).first()
            
            if has_taught_subject:
                score += 5
                reason = f"Recommended: Teaches {req.subject_needed}"

        if is_available:
            candidates.append({
                "id": teacher.id,
                "name": teacher.full_name,
                "score": score,
                "reason": reason,
                "phone": teacher.phone_number
            })

    # Sort: Highest score first
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates

@app.get("/grades/analytics/{class_name}")
def get_class_analytics(class_name: str, db: Session = Depends(get_db)):
    """
    Get all grades for a specific class, organized by student.
    Used for the Class Analytics Dashboard.
    """
    # 1. Get all students in this class
    students = db.query(Student).filter(Student.class_name == class_name).all()
    
    analytics_data = []
    
    for s in students:
        # Get grades for this student
        grades = db.query(Grade).filter(Grade.student_id == s.id).all()
        
        if not grades:
            continue
            
        # Calculate stats
        total_score = sum(g.score for g in grades)
        avg_score = total_score / len(grades)
        
        # Check for failed subjects (< 40 marks)
        failed_subjects = [g.subject for g in grades if g.score < 40]
        
        analytics_data.append({
            "id": s.id,
            "name": s.full_name,
            "average": round(avg_score, 1),
            "failed_count": len(failed_subjects),
            "failed_subjects": failed_subjects
        })
    
    # Sort: Lowest average first (so teachers see 'At Risk' students at the top)
    analytics_data.sort(key=lambda x: x['average'])
    
    return analytics_data