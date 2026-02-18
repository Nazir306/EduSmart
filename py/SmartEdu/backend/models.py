from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Time, Date
from sqlalchemy.orm import relationship
from datetime import datetime

# 👇 CRITICAL CHANGE: We import Base from database.py instead of creating it here
from .database import Base

# --- TABLE DEFINITIONS ---

class User(Base):
    """
    Stores Teachers and Admins.
    Role: 'admin' or 'teacher'
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(String, default="teacher") 
    phone_number = Column(String, nullable=True)
    
    # Relationships
    schedules = relationship("Schedule", back_populates="teacher")
    availabilities = relationship("TeacherAvailability", back_populates="teacher")
    attendance_logs = relationship("TeacherAttendance", back_populates="teacher")

    leaves_requested = relationship("LeaveRequest", foreign_keys="[LeaveRequest.teacher_id]", back_populates="teacher")
    substitute_assignments = relationship("LeaveRequest", foreign_keys="[LeaveRequest.substitute_teacher_id]", back_populates="substitute")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    class_name = Column(String)
    
    grades = relationship("Grade", back_populates="student")
    attendance = relationship("StudentAttendance", back_populates="student")

# --- MODULE B: SCHEDULING ---

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    day_of_week = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    subject = Column(String)
    room = Column(String)

    teacher = relationship("User", back_populates="schedules")

class TeacherAvailability(Base):
    __tablename__ = "teacher_availability"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    day_of_week = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    status = Column(String)

    teacher = relationship("User", back_populates="availabilities")

# --- MODULE A: LEAVES ---

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Path 1: The Requestor
    teacher_id = Column(Integer, ForeignKey("users.id"))
    
    # Path 2: The Substitute
    substitute_teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    date = Column(Date)
    reason = Column(String)
    status = Column(String, default="PENDING")

    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="leaves_requested")
    substitute = relationship("User", foreign_keys=[substitute_teacher_id], back_populates="substitute_assignments")

# --- MODULE C & D: ATTENDANCE ---

class TeacherAttendance(Base):
    __tablename__ = "teacher_attendance"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    clock_in_time = Column(DateTime, default=datetime.now)
    clock_out_time = Column(DateTime, nullable=True)

    teacher = relationship("User", back_populates="attendance_logs")

class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date)
    is_present = Column(Boolean, default=False)

    student = relationship("Student", back_populates="attendance")

# --- MODULE E: GRADES ---

class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(String)
    score = Column(Float)
    term = Column(String)

    student = relationship("Student", back_populates="grades")