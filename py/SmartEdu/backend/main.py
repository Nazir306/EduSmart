from fastapi import FastAPI
from .database import engine, Base
from .routers import users, attendance, grades, schedule

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include the routers
app.include_router(users.router)
app.include_router(attendance.router)
app.include_router(grades.router)
app.include_router(schedule.router)

@app.get("/")
def read_root():
    return {"message": "System Online"}