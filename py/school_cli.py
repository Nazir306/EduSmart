import sqlite3

class SchoolManager:
    def __init__(self, db_name='school.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize database with Student and Grade tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # 1. Students Table
            cursor.execute('''
               CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. Grades Table (Linked to Students)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    subject TEXT NOT NULL,
                    score REAL,
                    term TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
                )
            ''')

    def add_student(self, full_name, class_name):
        """Add a new student"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO students (full_name, class_name)
                    VALUES (?, ?)
                ''', (full_name, class_name))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None

    def add_grade(self, student_id, subject, score, term="Finals"):
        """Add a grade for a specific student"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO grades(student_id, subject, score, term)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, subject, score, term))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        
    def get_all_students(self):
        """View all students"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students')
            return cursor.fetchall()
        
    def get_student_report(self, student_id):
        """Get all grades for a specific student"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.subject, g.score, g.term
                FROM grades g
                WHERE g.student_id = ?
                ORDER BY g.subject ASC
            ''', (student_id,))
            return cursor.fetchall()
        
    def delete_student(self, student_id):
        """Delete a student and ALL their grades (Cascade)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Note: We must enable foreign keys for ON DELETE CASCADE to work in SQLite
            cursor.execute("PRAGMA foreign_keys = ON") 
            cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
            return cursor.rowcount > 0

# --- CLI INTERFACE ---

def display_menu():
    print("\n" + "="*40)
    print("      🏫 SCHOOL MANAGEMENT CLI")
    print("="*40)
    print("1. Add New Student")
    print("2. View All Students")
    print("3. Add Grade to Student")
    print("4. View Student Report Card")
    print("5. Delete Student")
    print("6. Exit")
    print("-"*40)

def main():
    db = SchoolManager()

    while True:
        display_menu()
        choice = input("Enter selection (1-6): ").strip()

        if choice == '1':
            print("\n--- Add Student ---")
            name = input("Student Name: ").strip()
            cls = input("Class (e.g., 5 Science): ").strip()
            if name and cls:
                sid = db.add_student(name, cls)
                print(f"✅ Student Added! ID: {sid}")
            else:
                print("❌ Name and Class are required.")

        elif choice == '2':
            print("\n--- Student List ---")
            students = db.get_all_students()
            if students:
                print(f"{'ID':<5} | {'Name':<20} | {'Class':<10}")
                print("-" * 40)
                for s in students:
                    print(f"{s[0]:<5} | {s[1]:<20} | {s[2]:<10}")
            else:
                print("No students found.")

        elif choice == '3':
            print("\n--- Add Grade ---")
            try:
                sid = int(input("Student ID: ").strip())
                subj = input("Subject: ").strip()
                score = float(input("Score (0-100): ").strip())
                
                gid = db.add_grade(sid, subj, score)
                if gid:
                    print(f"✅ Grade Recorded! Grade ID: {gid}")
                else:
                    print("❌ Failed to add grade. Check Student ID.")
            except ValueError:
                print("❌ Invalid input. ID and Score must be numbers.")

        elif choice == '4':
            print("\n--- Report Card ---")
            try:
                sid = int(input("Enter Student ID: ").strip())
                grades = db.get_student_report(sid)
                if grades:
                    print(f"\nGrades for Student #{sid}:")
                    for g in grades:
                        # g[0]=Subject, g[1]=Score, g[2]=Term
                        status = "PASS" if g[1] >= 40 else "FAIL"
                        print(f"• {g[0]}: {g[1]}% ({status})")
                else:
                    print("No grades found for this student.")
            except ValueError:
                print("❌ Invalid ID.")

        elif choice == '5':
            print("\n--- Delete Student ---")
            try:
                sid = int(input("Enter Student ID to delete: ").strip())
                confirm = input("⚠️ This will delete the student AND their grades. Confirm? (y/n): ")
                if confirm.lower() == 'y':
                    if db.delete_student(sid):
                        print("✅ Student deleted.")
                    else:
                        print("❌ Student not found.")
            except ValueError:
                print("❌ Invalid ID.")

        elif choice == '6':
            print("Exiting... Good luck with your assignment!")
            break
        
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()