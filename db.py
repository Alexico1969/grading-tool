import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")

    conn.execute('CREATE TABLE IF NOT EXISTS students (first_name TEXT, last_name TEXT, group TEXT)')
    print("Table created successfully")
    conn.close()

def insert_student(first_name, last_name, group):
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    conn.execute("INSERT INTO students (first_name, last_name, group) VALUES (?, ?, ?)", (first_name, last_name, group))
    conn.commit()
    print("Records created successfully")
    conn.close()

def get_students():
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    cursor = conn.execute("SELECT first_name, last_name, group from students")
    students = []
    for row in cursor:
        students.append(row)
    conn.close()
    return students

def get_student(first_name, last_name):
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    cursor = conn.execute("SELECT first_name, last_name, group from students WHERE first_name = ? AND last_name = ?", (first_name, last_name))
    student = None
    for row in cursor:
        student = row
    conn.close()
    return student

def update_student(first_name, last_name, group):
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    conn.execute("UPDATE students SET group = ? WHERE first_name = ? AND last_name = ?", (group, first_name, last_name))
    conn.commit()
    print("Records updated successfully")
    conn.close()

def delete_student(first_name, last_name):
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    conn.execute("DELETE from students WHERE first_name = ? AND last_name = ?", (first_name, last_name))
    conn.commit()
    print("Records deleted successfully")
    conn.close()

