from pydantic import BaseModel
from typing import Optional # You might need this later, good to have

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