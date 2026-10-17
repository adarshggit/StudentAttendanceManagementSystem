
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import mysql.connector
from db_config import get_connection


# ==================================================
# DATABASE HELPER
# ==================================================

def run_query(query, values=None, fetch=False):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values or ())

        if fetch:
            return cursor.fetchall()

        connection.commit()
        return True

    except mysql.connector.Error as error:
        if connection:
            connection.rollback()

        messagebox.showerror("Database Error", str(error))
        return None

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ==================================================
# STUDENT MANAGEMENT
# ==================================================

def clear_student_form():
    roll_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    class_entry.delete(0, tk.END)


def add_student():
    roll = roll_entry.get().strip()
    name = name_entry.get().strip()
    class_name = class_entry.get().strip()

    if not roll or not name or not class_name:
        messagebox.showwarning(
            "Missing Details",
            "Enter roll number, student name, and class."
        )
        return

    result = run_query(
        """
        INSERT INTO students (roll_no, name, class_name)
        VALUES (%s, %s, %s)
        """,
        (roll, name, class_name)
    )

    if result:
        messagebox.showinfo(
            "Success",
            "Student registered successfully!"
        )

        clear_student_form()
        load_students()
        load_attendance_students()
        load_report()


def load_students():
    for item in students_table.get_children():
        students_table.delete(item)

    rows = run_query(
        """
        SELECT id, roll_no, name, class_name
        FROM students
        ORDER BY roll_no
        """,
        fetch=True
    )

    if rows is not None:
        for row in rows:
            students_table.insert("", tk.END, values=row)


def delete_student():
    selected = students_table.selection()

    if not selected:
        messagebox.showwarning(
            "Select Student",
            "Select a student from the table first."
        )
        return

    row = students_table.item(selected[0], "values")
    student_id = row[0]

    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Delete {row[2]} and all their attendance records?"
    )

    if not confirm:
        return

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM attendance WHERE student_id = %s",
            (student_id,)
        )

        cursor.execute(
            "DELETE FROM students WHERE id = %s",
            (student_id,)
        )

        connection.commit()

        messagebox.showinfo(
            "Success",
            "Student and attendance records deleted."
        )

        load_students()
        load_attendance_students()
        load_report()

    except mysql.connector.Error as error:
        if connection:
            connection.rollback()

        messagebox.showerror("Database Error", str(error))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ==================================================
# TEACHER: TOTAL CLASSES CONDUCTED
# ==================================================

def update_total_classes():
    class_name = teacher_class_entry.get().strip()
    total_text = total_classes_entry.get().strip()

    if not class_name or not total_text:
        messagebox.showwarning(
            "Missing Details",
            "Enter the class name and total classes conducted."
        )
        return

    try:
        total = int(total_text)

        if total < 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Total classes must be a whole number of 0 or more."
        )
        return

    # Do not allow the teacher to set fewer classes than
    # the number of attendance dates already recorded.
    existing = run_query(
        """
        SELECT COUNT(DISTINCT attendance_date)
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        WHERE s.class_name = %s
        """,
        (class_name,),
        fetch=True
    )

    if existing is None:
        return

    recorded_dates = existing[0][0]

    if total < recorded_dates:
        messagebox.showerror(
            "Invalid Total",
            f"Attendance exists for {recorded_dates} distinct dates "
            f"for this class. Total classes cannot be less than "
            f"{recorded_dates}."
        )
        return

    result = run_query(
        """
        INSERT INTO class_sessions (class_name, total_classes)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE total_classes = %s
        """,
        (class_name, total, total)
    )

    if result:
        messagebox.showinfo(
            "Success",
            f"Total classes for {class_name} updated to {total}."
        )
        load_report()


# ==================================================
# DAILY ATTENDANCE
# ==================================================

def load_attendance_students():
    for item in attendance_table.get_children():
        attendance_table.delete(item)

    rows = run_query(
        """
        SELECT id, roll_no, name, class_name
        FROM students
        ORDER BY class_name, roll_no
        """,
        fetch=True
    )

    if rows is None:
        return

    for row in rows:
        attendance_table.insert(
            "",
            tk.END,
            values=(row[0], row[1], row[2], row[3], "Not Marked")
        )


def mark_selected(status):
    selected = attendance_table.selection()

    if not selected:
        messagebox.showwarning(
            "Select Student",
            "Select one or more students first."
        )
        return

    for item in selected:
        values = list(attendance_table.item(item, "values"))
        values[4] = status
        attendance_table.item(item, values=values)


def save_attendance():
    selected_date = date_entry.get().strip()
    selected_class = attendance_class_entry.get().strip()

    if not selected_class:
        messagebox.showwarning(
            "Select Class",
            "Enter the class name for attendance."
        )
        return

    try:
        attendance_date = date.fromisoformat(selected_date)
    except ValueError:
        messagebox.showerror(
            "Invalid Date",
            "Enter the date in YYYY-MM-DD format."
        )
        return

    if attendance_date > date.today():
        messagebox.showerror(
            "Invalid Date",
            "Attendance cannot be saved for a future date."
        )
        return

    # Only save students belonging to the selected class.
    all_items = attendance_table.get_children()
    records = []

    for item in all_items:
        values = attendance_table.item(item, "values")

        if values[3] != selected_class:
            continue

        if values[4] not in ("Present", "Absent"):
            messagebox.showwarning(
                "Attendance Incomplete",
                f"Mark {values[2]} as Present or Absent before saving."
            )
            return

        records.append(
            (int(values[0]), selected_date, values[4])
        )

    if not records:
        messagebox.showwarning(
            "No Students",
            "No students were found for this class."
        )
        return

    # Verify that the class has been entered by the teacher.
    class_rows = run_query(
        """
        SELECT total_classes
        FROM class_sessions
        WHERE class_name = %s
        """,
        (selected_class,),
        fetch=True
    )

    if class_rows is None:
        return

    if not class_rows:
        messagebox.showwarning(
            "Classes Not Set",
            "The teacher must first enter the total classes "
            "for this class in the Attendance Reports tab."
        )
        return

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Prevent attendance from being entered twice
        # for the same student and date.
        for student_id, record_date, status in records:
            cursor.execute(
                """
                SELECT id
                FROM attendance
                WHERE student_id = %s AND attendance_date = %s
                """,
                (student_id, record_date)
            )

            if cursor.fetchone():
                raise ValueError(
                    f"Attendance already exists for student ID "
                    f"{student_id} on {record_date}."
                )

        # Do not exceed the teacher's class count.
        cursor.execute(
            """
            SELECT COUNT(DISTINCT attendance_date)
            FROM attendance a
            JOIN students s ON s.id = a.student_id
            WHERE s.class_name = %s
            """,
            (selected_class,)
        )

        recorded_dates = cursor.fetchone()[0]
        total_classes = int(class_rows[0][0])

        if recorded_dates >= total_classes:
            raise ValueError(
                "All classes entered by the teacher already have "
                "attendance dates recorded for this class."
            )

        cursor.executemany(
            """
            INSERT INTO attendance
                (student_id, attendance_date, status)
            VALUES (%s, %s, %s)
            """,
            records
        )

        connection.commit()

        messagebox.showinfo(
            "Success",
            f"Attendance saved for {selected_class} "
            f"on {selected_date}."
        )

        load_report()
        load_attendance_students()

    except ValueError as error:
        if connection:
            connection.rollback()

        messagebox.showwarning(
            "Attendance Not Saved",
            str(error)
        )

    except mysql.connector.Error as error:
        if connection:
            connection.rollback()

        messagebox.showerror(
            "Database Error",
            str(error)
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ==================================================
# ATTENDANCE REPORTS
# ==================================================

def load_report():
    for item in report_table.get_children():
        report_table.delete(item)

    rows = run_query(
        """
        SELECT
            s.roll_no,
            s.name,
            s.class_name,
            COALESCE(cs.total_classes, 0) AS total_classes,
            COALESCE(SUM(a.status = 'Present'), 0) AS present_count
        FROM students s
        LEFT JOIN attendance a
            ON s.id = a.student_id
        LEFT JOIN class_sessions cs
            ON s.class_name = cs.class_name
        GROUP BY
            s.id, s.roll_no, s.name,
            s.class_name, cs.total_classes
        ORDER BY s.class_name, s.roll_no
        """,
        fetch=True
    )

    if rows is None:
        return

    low_count = 0

    for row in rows:
        roll_no = row[0]
        name = row[1]
        class_name = row[2]
        total_classes = int(row[3])
        present_count = int(row[4])

        # Calculate absent and percentage using teacher's total.
        absent_count = max(total_classes - present_count, 0)

        if total_classes > 0:
            percentage = round(
                present_count * 100.0 / total_classes, 2
            )
        else:
            percentage = 0.0

        if total_classes > 0 and percentage < 75:
            low_count += 1

        report_table.insert(
            "",
            tk.END,
            values=(
                roll_no,
                name,
                class_name,
                total_classes,
                present_count,
                absent_count,
                f"{percentage:.2f}%"
            )
        )

    low_label.config(
        text=f"Students below 75% attendance: {low_count}"
    )


# ==================================================
# APPLICATION WINDOW
# ==================================================

root = tk.Tk()
root.title("Student Attendance Management System")
root.geometry("1250x720")
root.minsize(950, 600)

root.configure(bg="#F2F5F9")

title_label = tk.Label(
    root,
    text="STUDENT ATTENDANCE MANAGEMENT SYSTEM",
    font=("Arial", 19, "bold"),
    bg="#17365D",
    fg="white",
    pady=15
)
title_label.pack(fill=tk.X)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


# ==================================================
# TAB 1: STUDENT MANAGEMENT
# ==================================================

student_tab = ttk.Frame(notebook, padding=12)
notebook.add(student_tab, text="Student Management")

student_form = ttk.LabelFrame(
    student_tab,
    text="Register Student",
    padding=12
)
student_form.pack(fill=tk.X, pady=8)

ttk.Label(student_form, text="Roll Number:").grid(
    row=0, column=0, padx=5, pady=7, sticky="w"
)
roll_entry = ttk.Entry(student_form, width=22)
roll_entry.grid(row=0, column=1, padx=5, pady=7)

ttk.Label(student_form, text="Student Name:").grid(
    row=0, column=2, padx=5, pady=7, sticky="w"
)
name_entry = ttk.Entry(student_form, width=25)
name_entry.grid(row=0, column=3, padx=5, pady=7)

ttk.Label(student_form, text="Class:").grid(
    row=1, column=0, padx=5, pady=7, sticky="w"
)
class_entry = ttk.Entry(student_form, width=22)
class_entry.grid(row=1, column=1, padx=5, pady=7)

ttk.Button(
    student_form,
    text="Add Student",
    command=add_student
).grid(row=1, column=2, padx=5, pady=7)

ttk.Button(
    student_form,
    text="Clear Form",
    command=clear_student_form
).grid(row=1, column=3, padx=5, pady=7)

students_table = ttk.Treeview(
    student_tab,
    columns=("ID", "Roll No", "Name", "Class"),
    show="headings"
)

for column in ("ID", "Roll No", "Name", "Class"):
    students_table.heading(column, text=column)
    students_table.column(
        column,
        width=160,
        anchor=tk.CENTER
    )

students_table.pack(fill=tk.BOTH, expand=True, pady=10)

student_buttons = ttk.Frame(student_tab)
student_buttons.pack(fill=tk.X, pady=5)

ttk.Button(
    student_buttons,
    text="Refresh Students",
    command=load_students
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    student_buttons,
    text="Delete Selected Student",
    command=delete_student
).pack(side=tk.LEFT, padx=5)


# ==================================================
# TAB 2: DAILY ATTENDANCE
# ==================================================

attendance_tab = ttk.Frame(notebook, padding=12)
notebook.add(attendance_tab, text="Daily Attendance")

attendance_form = ttk.LabelFrame(
    attendance_tab,
    text="Attendance Details",
    padding=10
)
attendance_form.pack(fill=tk.X, pady=8)

ttk.Label(
    attendance_form,
    text="Class:"
).grid(row=0, column=0, padx=5, pady=5)

attendance_class_entry = ttk.Entry(
    attendance_form,
    width=18
)
attendance_class_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(
    attendance_form,
    text="Date (YYYY-MM-DD):"
).grid(row=0, column=2, padx=5, pady=5)

date_entry = ttk.Entry(attendance_form, width=15)
date_entry.insert(0, date.today().isoformat())
date_entry.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(
    attendance_tab,
    text="Select students and mark their attendance."
).pack(anchor=tk.W, pady=5)

attendance_table = ttk.Treeview(
    attendance_tab,
    columns=("ID", "Roll No", "Name", "Class", "Status"),
    show="headings",
    selectmode="extended"
)

for column in ("ID", "Roll No", "Name", "Class", "Status"):
    attendance_table.heading(column, text=column)
    attendance_table.column(
        column,
        width=150,
        anchor=tk.CENTER
    )

attendance_table.pack(fill=tk.BOTH, expand=True, pady=10)

attendance_buttons = ttk.Frame(attendance_tab)
attendance_buttons.pack(fill=tk.X, pady=5)

ttk.Button(
    attendance_buttons,
    text="Mark Present",
    command=lambda: mark_selected("Present")
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    attendance_buttons,
    text="Mark Absent",
    command=lambda: mark_selected("Absent")
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    attendance_buttons,
    text="Refresh Students",
    command=load_attendance_students
).pack(side=tk.LEFT, padx=5)

ttk.Button(
    attendance_buttons,
    text="Save Attendance",
    command=save_attendance
).pack(side=tk.LEFT, padx=5)


# ==================================================
# TAB 3: ATTENDANCE REPORTS
# ==================================================

report_tab = ttk.Frame(notebook, padding=12)
notebook.add(report_tab, text="Attendance Reports")

teacher_frame = ttk.LabelFrame(
    report_tab,
    text="Teacher: Update Classes Conducted",
    padding=10
)
teacher_frame.pack(fill=tk.X, pady=8)

ttk.Label(
    teacher_frame,
    text="Class:"
).pack(side=tk.LEFT, padx=5)

teacher_class_entry = ttk.Entry(
    teacher_frame,
    width=18
)
teacher_class_entry.pack(side=tk.LEFT, padx=5)

ttk.Label(
    teacher_frame,
    text="Total Classes Conducted:"
).pack(side=tk.LEFT, padx=5)

total_classes_entry = ttk.Entry(
    teacher_frame,
    width=10
)
total_classes_entry.pack(side=tk.LEFT, padx=5)

ttk.Button(
    teacher_frame,
    text="Update Classes",
    command=update_total_classes
).pack(side=tk.LEFT, padx=5)

low_label = ttk.Label(
    report_tab,
    text="Students below 75% attendance: 0",
    font=("Arial", 12, "bold")
)
low_label.pack(anchor=tk.W, pady=10)

report_table = ttk.Treeview(
    report_tab,
    columns=(
        "Roll No",
        "Name",
        "Class",
        "Total Classes",
        "Present",
        "Absent",
        "Percentage"
    ),
    show="headings"
)

for column in (
    "Roll No",
    "Name",
    "Class",
    "Total Classes",
    "Present",
    "Absent",
    "Percentage"
):
    report_table.heading(column, text=column)
    report_table.column(
        column,
        width=140,
        anchor=tk.CENTER
    )

report_table.pack(fill=tk.BOTH, expand=True, pady=10)

ttk.Button(
    report_tab,
    text="Refresh Report",
    command=load_report
).pack(anchor=tk.W, pady=5)


# ==================================================
# START APPLICATION
# ==================================================

load_students()
load_attendance_students()
load_report()

root.mainloop()
